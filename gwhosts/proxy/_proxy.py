import os
import resource
from base64 import b64encode
from collections import deque
from functools import lru_cache
from logging import Logger
from select import select
from socket import socket, AF_INET, AF_INET6, SOCK_DGRAM, SOCK_STREAM
from struct import pack, unpack
from time import time
from typing import Any, Callable, Optional, cast
from collections.abc import Iterable, Iterator

from ._types import DNSDataMessage, LinkState, RTMEvent
from ..dns import QName, DNSParserError, RRType, parse, qname_to_str, answer_to_str, Answer
from ..network import (
    Address,
    Datagram,
    ExpiringAddress,
    GatewayInfo,
    IPAddress,
    IPBinary,
    Network,
    NetworkSize,
    TCPSocket,
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
        hostnames: set[QName],
        logger: Logger,
        ipv4_ifname: Optional[str] = None,
        ipv4_gateway: Optional[IPAddress] = None,
        ipv6_ifname: Optional[str] = None,
        ipv6_gateway: Optional[IPAddress] = None,
        to_addr: Address = Address("127.0.0.1", 8053),
        buff_size: int = 1232,
        timeout_in_seconds: int = 5,
    ) -> None:
        self._ipv4_ifname = ipv4_ifname
        self._ipv4_gateway = ipv4_gateway
        self._ipv6_ifname = ipv6_ifname
        self._ipv6_gateway = ipv6_gateway
        self._to_addr = to_addr
        self._buff_size = buff_size
        self._timeout_in_seconds = timeout_in_seconds
        self._hostnames: set[QName] = hostnames
        self._logger: Logger = logger
        self._free_pool: list[UDPSocket] = []
        self._input_pool: list[socket] = []
        self._tcp_client_pool: dict[socket, Iterator[Optional[Datagram]]] = {}
        self._regular_pool: dict[UDPSocket, ExpiringAddress] = {}
        self._routed_pool: dict[UDPSocket, ExpiringAddress] = {}
        self._queries_queue: deque[Datagram] = deque()
        self._ipv4_addresses: set[IPAddress] = set()
        self._ipv4_subnets: set[Network] = set()
        self._ipv6_addresses: set[IPAddress] = set()
        self._ipv6_subnets: set[Network] = set()
        self._netlink_event_handlers: dict[RTMEvent, Callable[[Netlink, dict[str, Any]], None]] = {
            RTMEvent.NEW_ROUTE: self._process_rtm_route,
            RTMEvent.DEL_ROUTE: self._process_rtm_route,
            RTMEvent.NEW_LINK: self._process_rtm_newlink,
        }
        rtm_route_handlers = (
            (RTMEvent.NEW_ROUTE, AF_INET, ipv4_gateway, self._ipv4_process_rtm_new_route),
            (RTMEvent.NEW_ROUTE, AF_INET6, ipv6_gateway, self._ipv6_process_rtm_new_route),
            (RTMEvent.DEL_ROUTE, AF_INET, ipv4_gateway, self._ipv4_process_rtm_del_route),
            (RTMEvent.DEL_ROUTE, AF_INET6, ipv6_gateway, self._ipv6_process_rtm_del_route),
        )
        self._rtm_route_handlers: dict[tuple[str, int, str], Callable[[Network], None]] = {
            (_event, _family, _gateway): _handler
            for _event, _family, _gateway, _handler in rtm_route_handlers
            if _gateway is not None
        }
        rtm_newlink_handlers = (
            (ipv4_ifname, LinkState.UP, self._process_rtm_newlink_up),
            (ipv4_ifname, LinkState.DOWN, self._process_rtm_newlink_down),
            (ipv6_ifname, LinkState.UP, self._process_rtm_newlink_up),
            (ipv6_ifname, LinkState.DOWN, self._process_rtm_newlink_down),
        )
        self._rtm_newlink_handlers: dict[tuple[str, str], Callable[[Netlink, str], None]] = {
            (_ifname, _state): _handler for _ifname, _state, _handler in rtm_newlink_handlers if _ifname is not None
        }
        self._preserved_ifnames: set[str] = set()
        self._netlink_to_network = {
            AF_INET: self._ipv4_netlink_to_network,
            AF_INET6: self._ipv6_netlink_to_network,
        }
        self._rr_type_to_gateway_info: dict[RRType, GatewayInfo] = {
            RRType.A: GatewayInfo(ifname=ipv4_ifname, address=ipv4_gateway),
            RRType.AAAA: GatewayInfo(ifname=ipv6_ifname, address=ipv6_gateway),
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
    def _active_pool(self) -> list[socket]:
        return [*self._input_pool, *self._tcp_client_pool, *self._regular_pool, *self._routed_pool]

    def _get_socket(self) -> UDPSocket:
        if len(self._free_pool):
            return self._free_pool.pop()

        _socket = UDPSocket()
        _socket.setblocking(False)

        return _socket

    def _match_hostname(self, hostname: QName) -> Optional[QName]:  # type: ignore[return]
        for level in range(len(hostname)):
            level_name = hostname[level:]
            if level_name in self._hostnames:
                self._hostnames.add(hostname)
                return QName(level_name)

    @property
    def ipv4_subnets(self) -> set[Network]:
        return self._ipv4_subnets

    @lru_cache(maxsize=4094)
    def _ipv4_in_subnets(self, address: IPBinary) -> bool:
        return any(address & subnet.mask == subnet.address for subnet in self.ipv4_subnets)

    def _ipv4_update_subnets(self, addresses: set[Network]) -> dict[Network, bool]:
        subnets = set(ipv4_reduce_subnets(addresses.union(self.ipv4_subnets)))
        updates = self._ipv4_subnets.symmetric_difference(subnets)

        return {subnet: subnet in subnets for subnet in updates}

    @property
    def ipv6_subnets(self) -> set[Network]:
        return self._ipv6_subnets

    @lru_cache(maxsize=4094)
    def _ipv6_in_subnets(self, address: IPBinary) -> bool:
        return any(address & subnet.mask == subnet.address for subnet in self.ipv6_subnets)

    def _ipv6_update_subnets(self, addresses: set[Network]) -> dict[Network, bool]:
        subnets = set(ipv6_reduce_subnets(addresses.union(self.ipv6_subnets)))
        updates = self._ipv6_subnets.symmetric_difference(subnets)

        return {subnet: subnet in subnets for subnet in updates}

    def _update_routes(self, queue: Iterable[DNSDataMessage]) -> tuple[dict[Network, bool], dict[Network, bool]]:
        ipv4_addresses: set[Network] = set()
        ipv6_addresses: set[Network] = set()

        for response, addr in queue:
            for answer in response.answers:
                if answer.rr_type == RRType.A:
                    address = ipv4_bytes_to_int(answer.rr_data)

                    if not self._ipv4_in_subnets(address):
                        ipv4_addresses.add(Network(address, IPV4_NETMASK_MAX))

                elif answer.rr_type == RRType.AAAA:
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
        data, addr, sock = datagram

        try:
            query = parse(data)

        except DNSParserError:
            self._logger.error("Failed to parse DNS query")
            self._log_how_to_reproduce(data)

            return

        remote = self._get_socket()
        remote.sendto(data, self._to_addr)

        domains = [q.name for q in query.questions]
        matches: dict[QName, Optional[QName]] = {hostname: self._match_hostname(hostname) for hostname in domains}
        all_matches: str = ", ".join(qname_to_str(match) for match in matches.values() if match is not None)

        if all_matches:
            self._routed_pool[remote] = ExpiringAddress(addr, time(), sock)

            for hostname in domains:
                match = matches[hostname]
                if match is None:
                    self._logger.info(f"Q:{query.header.id} ← {qname_to_str(hostname)} ({all_matches})")
                else:
                    self._logger.info(f"Q:{query.header.id} ← {qname_to_str(hostname)} ({qname_to_str(match)})")

        else:
            self._regular_pool[remote] = ExpiringAddress(addr, time(), sock)

            for hostname in domains:
                self._logger.info(f"Q:{query.header.id} ← {qname_to_str(hostname)} (*)")

    @staticmethod
    def _sanitize_free_pool(pool: list[UDPSocket]) -> None:
        while pool:
            pool.pop().close()

    def _sanitize_active_pool(self, pool: dict[UDPSocket, ExpiringAddress]) -> int:
        current_timestamp = time()
        expired_queries = 0

        for _socket in tuple(pool.keys()):
            if current_timestamp - pool[_socket].time > self._timeout_in_seconds:
                self._free_pool.append(_socket)
                del pool[_socket]
                expired_queries += 1

        return expired_queries

    def _udp_read(self, _socket: UDPSocket) -> Datagram:
        data, addr = _socket.recvfrom(self._buff_size)
        return Datagram(data, Address(*addr), _socket)

    def _release(self, _socket: UDPSocket) -> None:
        self._free_pool.append(_socket)

    def _udp_read_and_release(self, _socket: UDPSocket, pool: dict[UDPSocket, ExpiringAddress]) -> Datagram:
        data = self._udp_read(_socket).data
        self._release(_socket)
        expiring_address: ExpiringAddress = pool.pop(_socket)
        return Datagram(data, expiring_address.address, expiring_address.socket)

    def _get_gateway_info(self, answer: Answer) -> Optional[GatewayInfo]:
        return self._rr_type_to_gateway_info.get(answer.rr_type)

    def _parse_routed_responses(self, responses: list[Datagram]) -> Iterator[DNSDataMessage]:
        for data, addr, sock in responses:
            try:
                response = parse(data)

            except DNSParserError:
                self._logger.error("Failed to parse DNS response")
                self._log_how_to_reproduce(data)

            else:
                for answer in response.answers:
                    gateway_info = self._get_gateway_info(answer)

                    if gateway_info is None:
                        self._logger.info(f"R:{response.header.id} → {answer_to_str(answer)}")
                    else:
                        self._logger.info(
                            f"R:{response.header.id} → {answer_to_str(answer)}"
                            f" → {gateway_info.ifname} → {gateway_info.address}"
                        )

                yield DNSDataMessage(response, addr)

    def _parse_regular_responses(self, responses: list[Datagram]) -> None:
        for data, addr, sock in responses:
            try:
                response = parse(data)

            except DNSParserError:
                self._logger.error("Failed to parse DNS response")
                self._log_how_to_reproduce(data)

            else:
                for answer in response.answers:
                    self._logger.info(f"R:{response.header.id} → {answer_to_str(answer)}")

    @staticmethod
    def _send_responses(queue: list[Datagram]) -> None:
        for data, addr, sock in queue:
            if sock.type == SOCK_DGRAM:
                sock.sendto(data, addr)

            elif sock.type == SOCK_STREAM:
                sock.sendall(pack("!H", len(data)) + data)

            else:
                raise AttributeError(f"Unknown socket type {sock}")

    @staticmethod
    def _ipv4_netlink_to_network(address: IPAddress, length: NetworkSize) -> Network:
        return Network(
            address=ipv4_str_to_int(address),
            mask=ipv4_network_size_to_netmask(length),
        )

    def _ipv4_process_rtm_new_route(self, network: Network) -> None:
        """New IPv4 route is added"""
        self._ipv4_subnets.add(network)
        self._logger.info(f"network added {ipv4_network_to_str(network)}")

    def _ipv4_process_rtm_del_route(self, network: Network) -> None:
        """An existing IPv4 route is deleted"""
        if self._ipv4_ifname in self._preserved_ifnames:
            self._logger.info(f"network preserved {ipv4_network_to_str(network)}")
            return

        try:
            self._ipv4_subnets.remove(network)

        except KeyError as e:
            self._logger.exception(e)
            self._logger.info(f"network does not exists {ipv4_network_to_str(network)}")

        else:
            self._logger.info(f"network deleted {ipv4_network_to_str(network)}")

    @staticmethod
    def _ipv6_netlink_to_network(address: IPAddress, length: NetworkSize) -> Network:
        return Network(
            address=ipv6_str_to_int(address),
            mask=ipv6_network_size_to_netmask(length),
        )

    def _ipv6_process_rtm_new_route(self, network: Network) -> None:
        """New IPv6 route is added"""
        self._ipv6_subnets.add(network)
        self._logger.info(f"network added {ipv6_network_to_str(network)}")

    def _ipv6_process_rtm_del_route(self, network: Network) -> None:
        """An IPv6 existing route is deleted"""
        if self._ipv6_ifname in self._preserved_ifnames:
            self._logger.info(f"network preserved {ipv6_network_to_str(network)}")
            return

        try:
            self._ipv6_subnets.remove(network)

        except KeyError as e:
            self._logger.exception(e)
            self._logger.info(f"network does not exists {ipv6_network_to_str(network)}")

        else:
            self._logger.info(f"network deleted {ipv6_network_to_str(network)}")

    def _process_rtm_newlink(self, netlink: Netlink, message: dict[str, Any]) -> None:
        attrs = dict(message["attrs"])
        ifname = attrs["IFLA_IFNAME"]
        state = message["state"]
        key = ifname, state

        if key in self._rtm_newlink_handlers:
            self._rtm_newlink_handlers[key](netlink, ifname)

    def _process_rtm_newlink_up(self, netlink: Netlink, ifname: str) -> None:
        if ifname not in self._preserved_ifnames:
            return

        self._preserved_ifnames.remove(ifname)

        if ifname == self._ipv4_ifname and self._ipv4_gateway is not None:
            self._logger.info(f"restoring IPv4 routes via {self._ipv4_gateway}...")

            for _network in self._ipv4_subnets:
                netlink.ipv4_add_route(_network, self._ipv4_gateway)

        if ifname == self._ipv6_ifname and self._ipv6_gateway is not None:
            self._logger.info(f"restoring IPv6 routes via {self._ipv6_gateway}...")

            for _network in self._ipv6_subnets:
                netlink.ipv6_add_route(_network, self._ipv6_gateway)

    def _process_rtm_newlink_down(self, netlink: Netlink, ifname: str) -> None:
        self._preserved_ifnames.add(ifname)
        self._logger.info(f"interface preserved {ifname}")

    def _process_rtm_route(self, netlink: Netlink, message: dict[str, Any]) -> None:
        attrs = dict(message["attrs"])

        if "RTA_GATEWAY" in attrs:
            event = message["event"]
            family = message["family"]
            gateway = attrs["RTA_GATEWAY"]
            key = event, family, gateway

            if key in self._rtm_route_handlers:
                network = self._netlink_to_network[family](
                    address=attrs["RTA_DST"],
                    length=message["dst_len"],
                )
                self._rtm_route_handlers[key](network)

    def _process_netlink_message(self, netlink: Netlink, message: dict[str, Any]) -> None:
        event = message["event"]

        if event in self._netlink_event_handlers:
            self._netlink_event_handlers[event](netlink, message)

    def _process_ipv4_updates(self, netlink: Netlink, updates: dict[Network, bool]) -> None:
        if self._ipv4_gateway is not None:
            for network, exist in updates.items():
                if exist:
                    netlink.ipv4_add_route(network, self._ipv4_gateway)
                else:
                    netlink.ipv4_del_route(network, self._ipv4_gateway)

    def _process_ipv6_updates(self, netlink: Netlink, updates: dict[Network, bool]) -> None:
        if self._ipv6_gateway is not None:
            for network, exist in updates.items():
                if exist:
                    netlink.ipv6_add_route(network, self._ipv6_gateway)
                else:
                    netlink.ipv6_del_route(network, self._ipv6_gateway)

    @staticmethod
    def _tcp_read(_socket: socket, addr: Address) -> Iterator[Optional[Datagram]]:
        while _socket.fileno() != -1:
            length_bytes = _socket.recv(2)
            (length,) = unpack("!H", length_bytes)

            data: bytes = _socket.recv(length)

            while len(data) < length:
                yield None
                data += _socket.recv(length - len(data))

            yield Datagram(data, Address(*addr), _socket)

    def listen(self, addr: Address) -> None:
        with Netlink() as netlink:
            netlink.bind()
            self._input_pool.append(netlink)

            self._logger.info("loading existing IPv4 routes...")

            for _message in netlink.get_routes(family=AF_INET):
                self._process_netlink_message(netlink, _message)

            self._logger.info("loading existing IPv6 routes...")

            for _message in netlink.get_routes(family=AF_INET6):
                self._process_netlink_message(netlink, _message)

            with UDPSocket() as udp, TCPSocket() as tcp:
                udp.bind(addr)
                tcp.bind(addr)
                tcp.listen()
                self._input_pool.append(udp)
                self._input_pool.append(tcp)

                self._logger.info(f"proxy is listening at {addr.host}:{addr.port}")

                while True:
                    try:
                        ready_responses: list[Datagram] = []
                        routed_responses: list[Datagram] = []
                        datagram: Optional[Datagram]

                        r_ready, w_ready, x_ready = select(self._active_pool, [], [], self._timeout_in_seconds)

                        for _socket in r_ready:
                            if _socket is udp:
                                self._queries_queue.append(self._udp_read(udp))

                            elif _socket is tcp:
                                client_socket, addr = tcp.accept()
                                tcp_reader: Iterator[Optional[Datagram]] = self._tcp_read(client_socket, addr)

                                if (datagram := next(tcp_reader, None)) is not None:
                                    self._queries_queue.append(datagram)

                                else:
                                    self._tcp_client_pool[client_socket] = tcp_reader

                            elif _socket in self._tcp_client_pool:
                                if (datagram := next(self._tcp_client_pool[_socket], None)) is not None:
                                    self._queries_queue.append(datagram)
                                    del self._tcp_client_pool[_socket]

                            elif _socket in self._routed_pool:
                                routed_responses.append(
                                    self._udp_read_and_release(cast(UDPSocket, _socket), self._routed_pool)
                                )

                            elif _socket in self._regular_pool:
                                ready_responses.append(
                                    self._udp_read_and_release(cast(UDPSocket, _socket), self._regular_pool)
                                )

                            elif _socket is netlink:
                                for _message in netlink.get():
                                    self._process_netlink_message(netlink, _message)

                            else:
                                raise AttributeError("Unknown socket source")

                        expired_queries = self._sanitize_active_pool(self._routed_pool)
                        expired_queries += self._sanitize_active_pool(self._regular_pool)

                        if expired_queries:
                            self._logger.warning(f"{expired_queries} queries expired")

                        queued_queries = self._process_queued_queries()

                        if queued_queries:
                            self._logger.warning(f"{queued_queries} remaining queries")

                        self._sanitize_free_pool(self._free_pool)

                        self._parse_regular_responses(ready_responses)

                        if routed_responses:
                            dns_data_messages = self._parse_routed_responses(routed_responses)

                            ipv4_updates, ipv6_updates = self._update_routes(dns_data_messages)

                            ready_responses.extend(routed_responses)

                            self._process_ipv4_updates(netlink, ipv4_updates)
                            self._process_ipv6_updates(netlink, ipv6_updates)

                        if ready_responses:
                            self._send_responses(ready_responses)

                    except Exception as e:
                        self._logger.exception(e)
