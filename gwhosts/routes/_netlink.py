from pyroute2 import IPRoute
from socket import AF_INET
from gwhosts.network import (
    ipv4_int_to_str,
    netmask_to_network_size,
)
from gwhosts.network import IPAddress, Network
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
    rt_proto,
    rt_type,
)

from pyroute2.netlink.rtnl.rtmsg import rtmsg
from pyroute2.iproute.linux import DEFAULT_TABLE


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


def _msg_get_ipv4_routes() -> rtmsg:
    msg = rtmsg()
    msg["family"] = AF_INET
    msg["table"] = DEFAULT_TABLE
    return msg


def _msg_ipv4_route(netaddr: str, netsize: int, gateway: str) -> rtmsg:
    msg = rtmsg()
    msg["family"] = AF_INET
    msg["table"] = DEFAULT_TABLE
    msg["proto"] = rt_proto["static"]
    msg["type"] = rt_type["unicast"]
    msg["dst_len"] = netsize
    msg["attrs"] = [
        ("RTA_TABLE", DEFAULT_TABLE),
        ("RTA_DST", netaddr),
        ("RTA_GATEWAY", gateway),
    ]
    return msg


class Netlink(IPRoute):
    def __init__(self, *args, family=NETLINK_ROUTE, **kwargs):
        super().__init__(*args, family=family, **kwargs)

    def get_ipv4_routes(self) -> None:
        """ Get all ipv4 routes

        Event message example:
        {'family': 2, 'dst_len': 32, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 4, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '192.168.2.123'), ('RTA_GATEWAY', '192.168.2.1'), \
        ('RTA_OIF', 6)], 'header': {'length': 60, 'type': 24, 'flags': 1536, 'sequence_number': 0, 'pid': 3894248, \
        'error': None, 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_NEWROUTE'}
        """
        self.put(
            msg=_msg_get_ipv4_routes(),
            msg_type=RTM_GETROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP,
        )

    def add_ipv4_route(self, network: Network, gateway: IPAddress) -> None:
        """ Add an ipv4 route with the specified parameters
        :param network: Subnet
        :param gateway: Gateway

        Event message example:
        {'family': 2, 'dst_len': 32, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 4, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '192.168.2.123'), ('RTA_GATEWAY', '192.168.2.1'), \
        ('RTA_OIF', 6)], 'header': {'length': 60, 'type': 24, 'flags': 1536, 'sequence_number': 0, 'pid': 3894248, \
        'error': None, 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_NEWROUTE'}
        """
        self.put(
            msg=_msg_ipv4_route(
                netaddr=ipv4_int_to_str(network.address),
                netsize=netmask_to_network_size(network.mask),
                gateway=gateway,
            ),
            msg_type=RTM_NEWROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_REPLACE,
        )

    def del_ipv4_route(self, network: Network, gateway: IPAddress) -> None:
        """ Delete an ipv4 route that matches the specified parameters
        :param network: Subnet
        :param gateway: Gateway

        Event message example:
        {'family': 2, 'dst_len': 32, 'src_len': 0, 'tos': 0, 'table': 254, 'proto': 4, 'scope': 0, 'type': 1, \
        'flags': 0, 'attrs': [('RTA_TABLE', 254), ('RTA_DST', '192.168.2.123'), ('RTA_GATEWAY', '192.168.2.1'), \
        ('RTA_OIF', 6)], 'header': {'length': 60, 'type': 25, 'flags': 0, 'sequence_number': 0, 'pid': 3894248, \
        'error': None, 'stats': Stats(qsize=0, delta=0, delay=0)}, 'event': 'RTM_DELROUTE'}
        """
        self.put(
            msg=_msg_ipv4_route(
                netaddr=ipv4_int_to_str(network.address),
                netsize=netmask_to_network_size(network.mask),
                gateway=gateway,
            ),
            msg_type=RTM_DELROUTE,
            msg_flags=NLM_F_REQUEST | NLM_F_ACK,
        )
