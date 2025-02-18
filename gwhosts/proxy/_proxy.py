import os
import resource
from base64 import b64encode
from collections import deque
from functools import lru_cache
from logging import Logger
from select import select
from socket import socket, AF_INET, AF_INET6
from time import time
from typing import Callable, Dict, Iterable, Iterator, List, Set, Tuple, Optional

from ._types import DNSDataMessage, RTMEvent
from ..dns import QName, DNSParserError, RRType, parse, qname_to_str, answer_to_str
from ..network import (
    Address,
    Datagram,
    ExpiringAddress,
    IPAddress,
    IPBinary,
    Network,
    NetworkSize,
    UDPSocket,
)
from ..network.ipv4 import (
    IPV4_NETMASK_MAX,
    ipv4_bytes_to_int,
    ipv4_str_to_int,
    ipv4_network_size_to_netmask,
    ipv4_network_to_str,
    ipv4_reduce_subnets,
)
from ..network.ipv6 import (
    IPV6_NETMASK_MAX,
    ipv6_bytes_to_int,
    ipv6_str_to_int,
    ipv6_network_size_to_netmask,
    ipv6_network_to_str,
    ipv6_reduce_subnets,
)
from ..routes import Netlink


class DNSProxy:
    def __init__(
        self,
        gateway: IPAddress,
        hostnames: Set[QName],
        logger: Logger,
        ipv6_gateway: Optional[IPAddress] = None,
        to_addr: Address = Address("127.0.0.1", 8053),
        buff_size: int = 1024,
        timeout_in_seconds: int = 5,
    ) -> None:
        self._ipv4_gateway = gateway
        self._ipv6_gateway = ipv6_gateway
        self._to_addr = to_addr
        self._buff_size = buff_size
        self._timeout_in_seconds = timeout_in_seconds
        self._hostnames: Set[QName] = hostnames
        self._logger: Logger = logger
        self._free_pool: List[UDPSocket] = []
        self._input_pool: List[UDPSocket] = []
        self._regular_pool: Dict[UDPSocket, ExpiringAddress] = {}
        self._routed_pool: Dict[UDPSocket, ExpiringAddress] = {}
        self._queries_queue: deque = deque()
        self._ipv4_addresses: Set[IPAddress] = set()
        self._ipv4_subnets: Set[Network] = set()
        self._ipv6_addresses: Set[IPAddress] = set()
        self._ipv6_subnets: Set[Network] = set()
        self._netlink_event_handlers: Dict[RTMEvent, Dict[Tuple[int, str], Callable]] = {
            RTMEvent.NEW_ROUTE.value: {
                (AF_INET, self._ipv4_gateway): self._ipv4_process_rtm_new_route,
                (AF_INET6, self._ipv6_gateway): self._ipv6_process_rtm_new_route,
            },
            RTMEvent.DEL_ROUTE.value: {
                (AF_INET, self._ipv4_gateway): self._ipv4_process_rtm_del_route,
                (AF_INET6, self._ipv6_gateway): self._ipv6_process_rtm_del_route,
            },
        }
        self._netlink_to_network = {
            AF_INET: self._ipv4_netlink_to_network,
            AF_INET6: self._ipv6_netlink_to_network,
        }

    @property
    def _open_files_count(self) -> int:
        """:return: The number of open file descriptors"""
        open_files = os.listdir("/proc/self/fd")

        return len(open_files)

    @property
    def _max_open_files_count(self) -> int:
        """:return: Current soft limit on the number of open file descriptors"""
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

        return soft

    @property
    def _active_pool(self):
        return [*self._input_pool, *self._regular_pool, *self._routed_pool]

    def _get_socket(self) -> UDPSocket:
        if len(self._free_pool):
            return self._free_pool.pop()

        _socket = UDPSocket()
        _socket.setblocking(False)

        return _socket

    def _hostname_exists(self, hostname: QName) -> bool:
        for level in range(len(hostname)):
            if hostname[level:] in self._hostnames:
                self._hostnames.add(hostname)
                return True

        return False

    @property
    def ipv4_subnets(self) -> Set[Network]:
        return self._ipv4_subnets

    @lru_cache(maxsize=4094)
    def _ipv4_in_subnets(self, address: IPBinary) -> bool:
        return any(address & subnet.mask == subnet.address for subnet in self.ipv4_subnets)

    def _ipv4_update_subnets(self, addresses: Set[Network]) -> Dict[Network, bool]:
        subnets = set(ipv4_reduce_subnets(addresses.union(self.ipv4_subnets)))
        updates = self._ipv4_subnets.symmetric_difference(subnets)

        return {subnet: subnet in subnets for subnet in updates}

    @property
    def ipv6_subnets(self) -> Set[Network]:
        return self._ipv6_subnets

    @lru_cache(maxsize=4094)
    def _ipv6_in_subnets(self, address: IPBinary) -> bool:
        return any(address & subnet.mask == subnet.address for subnet in self.ipv6_subnets)

    def _ipv6_update_subnets(self, addresses: Set[Network]) -> Dict[Network, bool]:
        subnets = set(ipv6_reduce_subnets(addresses.union(self.ipv6_subnets)))
        updates = self._ipv6_subnets.symmetric_difference(subnets)

        return {subnet: subnet in subnets for subnet in updates}

    def _update_routes(self, queue: Iterable[DNSDataMessage]) -> Tuple[Dict[Network, bool], Dict[Network, bool]]:
        ipv4_addresses = set()
        ipv6_addresses = set()

        for response, addr in queue:
            for answer in response.answers:
                if answer.rr_type == RRType.A.value:
                    address = ipv4_bytes_to_int(answer.rr_data)

                    if not self._ipv4_in_subnets(address):
                        ipv4_addresses.add(Network(address, IPV4_NETMASK_MAX))

                elif answer.rr_type == RRType.AAAA.value:
                    address = ipv6_bytes_to_int(answer.rr_data)

                    if not self._ipv6_in_subnets(address):
                        ipv6_addresses.add(Network(address, IPV6_NETMASK_MAX))

        return (
            self._ipv4_update_subnets(ipv4_addresses) if ipv4_addresses else {},
            self._ipv6_update_subnets(ipv6_addresses) if ipv6_addresses else {},
        )

    def _process_queued_queries(self) -> int:
        """Process queued queries and return the number of remaining ones

        :return: Number of remaining queries
        """
        queue_size = len(self._queries_queue)
        available_file_descriptors_count = self._max_open_files_count - self._open_files_count

        for _ in range(min(queue_size, available_file_descriptors_count)):
            self._route_request(self._queries_queue.popleft())

        return len(self._queries_queue)

    def _log_how_to_reproduce(self, data: bytes) -> None:
        b64data = b64encode(data).decode("utf8")
        self._logger.error("To reproduce, run:")
        self._logger.error(f"echo -n '{b64data}' | python -m base64 -d | python -m gwhosts.dns.parser")

    def _route_request(self, datagram: Datagram) -> None:
        data, addr = datagram

        try:
            query = parse(data)

        except DNSParserError:
            self._logger.error("Failed to parse DNS query")
            self._log_how_to_reproduce(data)

            return

        remote = self._get_socket()
        remote.sendto(data, self._to_addr)

        domains = [q.name for q in query.questions]

        if any(self._hostname_exists(hostname) for hostname in domains):
            self._routed_pool[remote] = ExpiringAddress(addr, time())

            for hostname in domains:
                self._logger.info(f"DNS: Q[{query.header.id}] -> {qname_to_str(hostname)} (P)")

        else:
            self._regular_pool[remote] = ExpiringAddress(addr, time())

            for hostname in domains:
                self._logger.info(f"DNS: Q[{query.header.id}] -> {qname_to_str(hostname)}")

    @staticmethod
    def _sanitize_free_pool(pool: List[socket]) -> None:
        while pool:
            pool.pop().close()

    def _sanitize_active_pool(self, pool: Dict[UDPSocket, ExpiringAddress]) -> int:
        current_timestamp = time()
        expired_queries = 0

        for _socket in tuple(pool.keys()):
            if current_timestamp - pool[_socket].time > self._timeout_in_seconds:
                self._free_pool.append(_socket)
                del pool[_socket]
                expired_queries += 1

        return expired_queries

    def _read(self, _socket: socket) -> Datagram:
        data, addr = _socket.recvfrom(self._buff_size)
        return Datagram(data, Address(*addr))

    def _release(self, _socket: UDPSocket) -> None:
        self._free_pool.append(_socket)

    def _read_and_release(self, _socket: UDPSocket, pool: Dict[UDPSocket, ExpiringAddress]) -> Datagram:
        data = self._read(_socket).data
        self._release(_socket)
        return Datagram(data, pool.pop(_socket).address)

    def _parse_responses(self, responses: List[Datagram]) -> Iterator[DNSDataMessage]:
        for data, addr in responses:
            try:
                response = parse(data)

            except DNSParserError:
                self._logger.error("Failed to parse DNS response")
                self._log_how_to_reproduce(data)

            else:
                for answer in response.answers:
                    self._logger.info(f"DNS: R[{response.header.id}] {answer_to_str(answer)}")

                yield DNSDataMessage(response, addr)

    @staticmethod
    def _send_responses(queue: List[Datagram], udp: UDPSocket) -> None:
        for data, addr in queue:
            udp.sendto(data, addr)

    @staticmethod
    def _ipv4_netlink_to_network(address: IPAddress, length: NetworkSize) -> Network:
        return Network(
            address=ipv4_str_to_int(address),
            mask=ipv4_network_size_to_netmask(length),
        )

    def _ipv4_process_rtm_new_route(self, network: Network) -> None:
        """New IPv4 route is added"""
        self._ipv4_subnets.add(network)
        self._logger.info(f"DNS: network added {ipv4_network_to_str(network)}")

    def _ipv4_process_rtm_del_route(self, network: Network) -> None:
        """An existing IPv4 route is deleted"""
        try:
            self._ipv4_subnets.remove(network)

        except KeyError as e:
            self._logger.exception(e)
            self._logger.info(f"DNS: network does not exists {ipv4_network_to_str(network)}")

        else:
            self._logger.info(f"DNS: network deleted {ipv4_network_to_str(network)}")

    @staticmethod
    def _ipv6_netlink_to_network(address: IPAddress, length: NetworkSize) -> Network:
        return Network(
            address=ipv6_str_to_int(address),
            mask=ipv6_network_size_to_netmask(length),
        )

    def _ipv6_process_rtm_new_route(self, network: Network) -> None:
        """New IPv6 route is added"""
        self._ipv6_subnets.add(network)
        self._logger.info(f"DNS: network added {ipv6_network_to_str(network)}")

    def _ipv6_process_rtm_del_route(self, network: Network) -> None:
        """An IPv6 existing route is deleted"""
        try:
            self._ipv6_subnets.remove(network)

        except KeyError as e:
            self._logger.exception(e)
            self._logger.info(f"DNS: network does not exists {ipv6_network_to_str(network)}")

        else:
            self._logger.info(f"DNS: network deleted {ipv6_network_to_str(network)}")

    def _process_netlink_message(self, message: dict) -> None:
        event = message["event"]

        if event in self._netlink_event_handlers:
            attrs = dict(message["attrs"])

            if "RTA_GATEWAY" in attrs:
                event_handlers = self._netlink_event_handlers[event]
                family = message["family"]

                if family in self._netlink_to_network:
                    gateway = attrs["RTA_GATEWAY"]

                    if (family, gateway) in event_handlers:
                        network = self._netlink_to_network[family](
                            address=attrs["RTA_DST"],
                            length=message["dst_len"],
                        )
                        event_handlers[(family, gateway)](network)

    def listen(self, addr: Address) -> None:
        with Netlink() as netlink:
            netlink.bind()
            self._input_pool.append(netlink)

            self._logger.info(f"DNS: loading existing IPv4 routes via {self._ipv4_gateway}...")

            for _message in netlink.get_routes(family=AF_INET):
                self._process_netlink_message(_message)

            self._logger.info(f"DNS: loading existing IPv6 routes via {self._ipv6_gateway}...")

            for _message in netlink.get_routes(family=AF_INET6):
                self._process_netlink_message(_message)

            netlink.ipv4_get_routes()
            netlink.ipv6_get_routes()

            with UDPSocket() as udp:
                udp.bind(addr)
                self._input_pool.append(udp)

                self._logger.info(f"DNS: proxy is listening at {addr.host}:{addr.port}")

                while True:
                    try:
                        ready_responses: List[Datagram] = []
                        routed_responses: List[Datagram] = []

                        r_ready, w_ready, x_ready = select(self._active_pool, [], [], self._timeout_in_seconds)

                        for _socket in r_ready:
                            if _socket is udp:
                                self._queries_queue.append(self._read(_socket))

                            elif _socket in self._routed_pool:
                                routed_responses.append(self._read_and_release(_socket, self._routed_pool))

                            elif _socket in self._regular_pool:
                                ready_responses.append(self._read_and_release(_socket, self._regular_pool))

                            elif _socket is netlink:
                                for _message in netlink.get():
                                    self._process_netlink_message(_message)

                            else:
                                raise AttributeError("DNS: Unknown socket source")

                        expired_queries = self._sanitize_active_pool(self._routed_pool)
                        expired_queries += self._sanitize_active_pool(self._regular_pool)

                        if expired_queries:
                            self._logger.warning(f"DNS: {expired_queries} queries expired")

                        queued_queries = self._process_queued_queries()

                        if queued_queries:
                            self._logger.warning(f"DNS: {queued_queries} remaining queries")

                        self._sanitize_free_pool(self._free_pool)

                        if routed_responses:
                            dns_data_messages = self._parse_responses(routed_responses)

                            ipv4_updates, ipv6_updates = self._update_routes(dns_data_messages)

                            ready_responses.extend(routed_responses)

                            for network, exist in ipv4_updates.items():
                                if exist:
                                    netlink.ipv4_add_route(network, self._ipv4_gateway)
                                else:
                                    netlink.ipv4_del_route(network, self._ipv4_gateway)

                            for network, exist in ipv6_updates.items():
                                if exist:
                                    netlink.ipv6_add_route(network, self._ipv6_gateway)
                                else:
                                    netlink.ipv6_del_route(network, self._ipv6_gateway)

                        if ready_responses:
                            self._send_responses(ready_responses, udp)

                    except Exception as e:
                        self._logger.exception(e)
