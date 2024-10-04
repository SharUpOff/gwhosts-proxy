from socket import AF_INET, AF_INET6

from pyroute2 import IPRoute
from pyroute2.netlink import (
    NLM_F_ACK,
    NLM_F_APPEND,
    NLM_F_ATOMIC,
    NLM_F_CREATE,
    NLM_F_DUMP,
    NLM_F_ECHO,
    NLM_F_EXCL,
    NLM_F_REPLACE,
    NLM_F_REQUEST,
    NLM_F_ROOT,
    NLMSG_ERROR,
    NETLINK_ROUTE,
)
from pyroute2.netlink.rtnl import (
    RTM_DELROUTE,
    RTM_GETROUTE,
    RTM_NEWROUTE,
)
from pyroute2.netlink.rtnl.rtmsg import rtmsg

from ._rtmsg import _msg_get_routes, _msg_route
from ..network import IPAddress, Network
from ..network.ipv4 import (
    ipv4_int_to_str,
    ipv4_netmask_to_network_size,
)
from ..network.ipv6 import (
    ipv6_int_to_str,
    ipv6_netmask_to_network_size,
)

__all__ = [
    "NLM_F_ACK",
    "NLM_F_APPEND",
    "NLM_F_ATOMIC",
    "NLM_F_CREATE",
    "NLM_F_DUMP",
    "NLM_F_ECHO",
    "NLM_F_EXCL",
    "NLM_F_REPLACE",
    "NLM_F_REQUEST",
    "NLM_F_ROOT",
    "NLMSG_ERROR",
    "NETLINK_ROUTE",
]


def _ipv4_msg_get_routes() -> rtmsg:
    return _msg_get_routes(AF_INET)


def _ipv4_msg_route(netaddr: str, netsize: int, gateway: str) -> rtmsg:
    return _msg_route(netaddr, netsize, gateway, AF_INET)


def _ipv6_msg_get_routes() -> rtmsg:
    return _msg_get_routes(AF_INET6)


def _ipv6_msg_route(netaddr: str, netsize: int, gateway: str) -> rtmsg:
    return _msg_route(netaddr, netsize, gateway, AF_INET6)


class Netlink(IPRoute):
    def __init__(self, *args, family=NETLINK_ROUTE, **kwargs):
        super().__init__(*args, family=family, **kwargs)

    def ipv4_get_routes(self) -> None:
        """ Get all ipv4 routes

        Shell command example:
        ip r

        Event message example:
        {'family': 2, 'dst_len': 32, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 4, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '192.168.2.123'), ('RTA_GATEWAY', '192.168.2.1'), \
        ('RTA_OIF', 6)], 'header': {'length': 60, 'type': 24, 'flags': 1536, 'sequence_number': 0, 'pid': 3894248, \
        'error': None, 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_NEWROUTE'}
        """
        self.put(
            msg=_ipv4_msg_get_routes(),
            msg_type=RTM_GETROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP,
        )

    def ipv4_add_route(self, network: Network, gateway: IPAddress) -> None:
        """ Add an ipv4 route with the specified parameters
        :param network: Subnet
        :param gateway: Gateway

        Shell command example:
        ip r add 192.168.2.123/32 via 192.168.2.1

        Event message example:
        {'family': 2, 'dst_len': 32, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 4, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '192.168.2.123'), ('RTA_GATEWAY', '192.168.2.1'), \
        ('RTA_OIF', 6)], 'header': {'length': 60, 'type': 24, 'flags': 1536, 'sequence_number': 0, 'pid': 3894248, \
        'error': None, 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_NEWROUTE'}
        """
        self.put(
            msg=_ipv4_msg_route(
                netaddr=ipv4_int_to_str(network.address),
                netsize=ipv4_netmask_to_network_size(network.mask),
                gateway=gateway,
            ),
            msg_type=RTM_NEWROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_REPLACE,
        )

    def ipv4_del_route(self, network: Network, gateway: IPAddress) -> None:
        """ Delete an ipv4 route that matches the specified parameters
        :param network: Subnet
        :param gateway: Gateway

        Shell command example:
        ip r del 192.168.2.123/32 via 192.168.2.1

        Event message example:
        {'family': 2, 'dst_len': 32, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 4, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '192.168.2.123'), ('RTA_GATEWAY', '192.168.2.1'), \
        ('RTA_OIF', 6)], 'header': {'length': 60, 'type': 25, 'flags': 0, 'sequence_number': 0, 'pid': 3894248, \
        'error': None, 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_DELROUTE'}
        """
        self.put(
            msg=_ipv4_msg_route(
                netaddr=ipv4_int_to_str(network.address),
                netsize=ipv4_netmask_to_network_size(network.mask),
                gateway=gateway,
            ),
            msg_type=RTM_DELROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK,
        )

    def ipv6_get_routes(self) -> None:
        """ Get all ipv6 routes

        Shell command example:
        ip -6 r

        Event message example:
        {'family': 10, 'dst_len': 56, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 3, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '2a00:1450:4005:800::'), ('RTA_PRIORITY', 1024), \
        ('RTA_GATEWAY', 'fced:9999::1'), ('RTA_OIF', 91), ('RTA_CACHEINFO', {'rta_clntref': 0, 'rta_lastuse': 0, \
        'rta_expires': 0, 'rta_error': 0, 'rta_used': 0, 'rta_id': 0, 'rta_ts': 0, 'rta_tsage': 0}), ('RTA_PREF', 0)], \
        'header': {'length': 136, 'type': 24, 'flags': 1536, 'sequence_number': 1726729418, 'pid': 10120, \
        'error': None, 'target': 'localhost', 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_NEWROUTE'}
        """
        self.put(
            msg=_ipv6_msg_get_routes(),
            msg_type=RTM_GETROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP,
        )

    def ipv6_add_route(self, network: Network, gateway: IPAddress) -> None:
        """ Add an ipv6 route with the specified parameters
        :param network: Subnet
        :param gateway: Gateway

        Shell command example:
        ip -6 r add 2a00:1450:4005:800::/56 via fced:9999::1

        Event message example:
        {'family': 10, 'dst_len': 56, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 3, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '2a00:1450:4005:800::'), ('RTA_PRIORITY', 1024), \
        ('RTA_GATEWAY', 'fced:9999::1'), ('RTA_OIF', 91), ('RTA_CACHEINFO', {'rta_clntref': 0, 'rta_lastuse': 0, \
        'rta_expires': 0, 'rta_error': 0, 'rta_used': 0, 'rta_id': 0, 'rta_ts': 0, 'rta_tsage': 0}), ('RTA_PREF', 0)], \
        'header': {'length': 136, 'type': 24, 'flags': 1536, 'sequence_number': 1726729418, 'pid': 10120, \
        'error': None, 'target': 'localhost', 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_NEWROUTE'}
        """
        self.put(
            msg=_ipv6_msg_route(
                netaddr=ipv6_int_to_str(network.address),
                netsize=ipv6_netmask_to_network_size(network.mask),
                gateway=gateway,
            ),
            msg_type=RTM_NEWROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_REPLACE,
        )

    def ipv6_del_route(self, network: Network, gateway: IPAddress) -> None:
        """ Delete an ipv6 route that matches the specified parameters
        :param network: Subnet
        :param gateway: Gateway

        Shell command example:
        ip -6 r del 2a00:1450:4005:800::/56 via fced:9999::1

        Event message example:
        {'family': 10, 'dst_len': 56, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 3, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '2a00:1450:4005:800::'), ('RTA_PRIORITY', 1024), \
        ('RTA_GATEWAY', 'fced:9999::1'), ('RTA_OIF', 91), ('RTA_CACHEINFO', {'rta_clntref': 0, 'rta_lastuse': 0, \
        'rta_expires': 0, 'rta_error': 0, 'rta_used': 0, 'rta_id': 0, 'rta_ts': 0, 'rta_tsage': 0}), ('RTA_PREF', 0)], \
        'header': {'length': 136, 'type': 25, 'flags': 0, 'sequence_number': 1726729519, 'pid': 15041, 'error': None, \
        'target': 'localhost', 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_DELROUTE'}
        """
        self.put(
            msg=_ipv6_msg_route(
                netaddr=ipv6_int_to_str(network.address),
                netsize=ipv6_netmask_to_network_size(network.mask),
                gateway=gateway,
            ),
            msg_type=RTM_DELROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK,
        )
