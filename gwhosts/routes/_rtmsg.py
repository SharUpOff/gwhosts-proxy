from pyroute2.netlink.rtnl.rtmsg import rtmsg
from pyroute2.iproute.linux import DEFAULT_TABLE
from pyroute2.netlink.rtnl import (
    rt_proto,
    rt_type,
)


def _msg_get_routes(family: int) -> rtmsg:
    msg = rtmsg()
    msg["family"] = family
    msg["table"] = DEFAULT_TABLE
    return msg


def _msg_route(netaddr: str, netsize: int, gateway: str, family: int) -> rtmsg:
    msg = rtmsg()
    msg["family"] = family
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
