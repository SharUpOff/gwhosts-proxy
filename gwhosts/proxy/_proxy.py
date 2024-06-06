import os
import resource
from collections import deque
from functools import lru_cache
from logging import Logger
from select import select
from socket import socket
from time import time
from typing import Callable, Dict, Iterator, List, Set, Tuple

from gwhosts.dns import QName, RRType, parse, remove_ipv6, serialize
from gwhosts.network import (
    NETMASK_MAX,
    Address,
    Datagram,
    ExpiringAddress,
    IPAddress,
    IPBinary,
    Network,
    UDPSocket,
    ipv4_bytes_to_int,
    ipv4_int_to_str,
    ipv4_str_to_int,
    network_size_to_netmask,
    network_to_str,
    reduce_subnets,
)
from gwhosts.proxy._types import DNSDataMessage, RTMEvent
from gwhosts.routes import Netlink


class DNSProxy:
    def __init__(
        self,
        gateway: IPAddress,
        hostnames: Set[QName],
        logger: Logger,
        to_addr: Address = Address("127.0.0.1", 8053),
        buff_size: int = 1024,
        timeout_in_seconds: int = 5,
    ) -> None:
        self._gateway = gateway
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
        self._addresses: Set[IPAddress] = set()
        self._subnets: Set[Network] = set()
        self._netlink_event_handlers: Dict[RTMEvent, Callable] = {
            RTMEvent.NEW_ROUTE.value: self._process_rtm_new_route,
            RTMEvent.DEL_ROUTE.value: self._process_rtm_del_route,
        }
        self._update_routes_queue: List[Tuple[Dict[Network, bool], List[Datagram]]] = []

    @property
    def _open_files_count(self) -> int:
        """ :return: The number of open file descriptors
        """
        open_files = os.listdir("/proc/self/fd")

        return len(open_files)

    @property
    def _max_open_files_count(self) -> int:
        """ :return: Current soft limit on the number of open file descriptors
        """
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

    @property
    def subnets(self) -> Set[Network]:
        return self._subnets

    @lru_cache(maxsize=4094)
    def _hostname_exists(self, hostname: QName) -> bool:
        for level in range(len(hostname)):
            if hostname[level:] in self._hostnames:
                return True

        return False

    @lru_cache(maxsize=4094)
    def _ip_in_subnets(self, address: IPBinary) -> bool:
        return any(address & subnet.mask == subnet.address for subnet in self.subnets)

    def _update_subnets(self, addresses: Set[Network]) -> dict[Network, bool]:
        subnets = set(reduce_subnets(addresses.union(self.subnets)))
        updates = self._subnets.symmetric_difference(subnets)

        return {subnet: subnet in subnets for subnet in updates}

    def _update_routes(self, queue: List[DNSDataMessage]) -> dict[Network, bool]:
        addresses = set()

        for response, addr in queue:
            for answer in response.answers:
                if answer.rr_type == RRType.A.value:
                    address = ipv4_bytes_to_int(answer.rr_data)

                    self._logger.info(f"DNS: {b'.'.join(answer.name).decode('utf8')} -> {ipv4_int_to_str(address)}")

                else:
                    continue

                if self._ip_in_subnets(address):
                    continue

                addresses.add(Network(address, NETMASK_MAX))

        if addresses:
            return self._update_subnets(addresses)

        return {}

    def _process_queued_queries(self) -> int:
        """ Process queued queries and return the number of remaining ones

            :return: Number of remaining queries
        """
        queue_size = len(self._queries_queue)
        available_file_descriptors_count = self._max_open_files_count - self._open_files_count

        for _ in range(min(queue_size, available_file_descriptors_count)):
            self._route_request(self._queries_queue.popleft())

        return len(self._queries_queue)

    def _route_request(self, datagram: Datagram) -> None:
        data, addr = datagram
        remote = self._get_socket()
        remote.sendto(data, self._to_addr)

        query = parse(data)
        domains = [q.name for q in query.questions]

        if any(self._hostname_exists(hostname) for hostname in domains):
            self._routed_pool[remote] = ExpiringAddress(addr, time())

            for hostname in domains:
                self._logger.info(f"DNS: [{query.header.id}] -> {b'.'.join(hostname).decode('utf8')}")

        else:
            self._regular_pool[remote] = ExpiringAddress(addr, time())

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

    @staticmethod
    def _parse_responses(responses: List[Datagram]) -> List[DNSDataMessage]:
        return [DNSDataMessage(parse(data), addr) for data, addr in responses]

    @staticmethod
    def _prepare_routed_responses(data_messages: List[DNSDataMessage]) -> Iterator[Datagram]:
        return (Datagram(serialize(remove_ipv6(data)), addr) for data, addr in data_messages)

    @staticmethod
    def _send_responses(queue: List[Datagram], udp: UDPSocket) -> None:
        for data, addr in queue:
            udp.sendto(data, addr)

    def _process_rtm_new_route(self, network: Network) -> None:
        """New route is added"""
        self._subnets.add(network)
        self._logger.info(f"DNS: network added {network_to_str(network)}")

    def _process_rtm_del_route(self, network: Network) -> None:
        """An existing route is deleted"""
        try:
            self._subnets.remove(network)

        except KeyError as e:
            self._logger.exception(e)
            self._logger.info(f"DNS: network does not exists {network_to_str(network)}")

        else:
            self._logger.info(f"DNS: network deleted {network_to_str(network)}")

    def _process_netlink_message(self, message: dict) -> None:
        event = message["event"]

        if event in self._netlink_event_handlers:
            attrs = dict(message["attrs"])

            if "RTA_GATEWAY" in attrs:
                if attrs["RTA_GATEWAY"] == self._gateway:
                    network = Network(
                        address=ipv4_str_to_int(attrs["RTA_DST"]),
                        mask=network_size_to_netmask(message["dst_len"]),
                    )

                    self._netlink_event_handlers[event](network)

    def listen(self, addr: Address) -> None:
        with Netlink() as netlink:
            netlink.bind()
            self._input_pool.append(netlink)

            self._logger.info("DNS: Getting routed subnets...")
            netlink.get_ipv4_routes()

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

                            updates = self._update_routes(dns_data_messages)

                            ready_responses.extend(self._prepare_routed_responses(dns_data_messages))

                            for network, exist in updates.items():
                                if exist:
                                    netlink.add_ipv4_route(network, self._gateway)
                                else:
                                    netlink.del_ipv4_route(network, self._gateway)

                        if ready_responses:
                            self._send_responses(ready_responses, udp)

                    except Exception as e:
                        self._logger.exception(e)
