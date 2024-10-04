from socket import AF_INET, AF_INET6

import pytest
from pyroute2.iproute.linux import DEFAULT_TABLE
from pyroute2.netlink import (
    NLM_F_ACK,
    NLM_F_CREATE,
    NLM_F_DUMP,
    NLM_F_REPLACE,
    NLM_F_REQUEST,
)
from pyroute2.netlink.rtnl import (
    RTM_DELROUTE,
    RTM_GETROUTE,
    RTM_NEWROUTE,
)
from pyroute2.netlink.rtnl import (
    rt_proto,
    rt_type,
)
from pyroute2.netlink.rtnl.rtmsg import rtmsg
from pytest_mock import MockerFixture

from gwhosts.network import Network, IPAddress
from gwhosts.network.ipv4 import ipv4_int_to_str, ipv4_netmask_to_network_size
from gwhosts.network.ipv6 import ipv6_int_to_str, ipv6_netmask_to_network_size
from gwhosts.routes import Netlink


@pytest.fixture
def netlink(mocker: MockerFixture) -> Netlink:
    mocker.patch("gwhosts.routes.Netlink.__init__", return_value=None)
    mocker.patch("gwhosts.routes.Netlink.put", return_value=None)
    return Netlink()


def test_ipv4_get_routes(netlink: Netlink) -> None:
    msg = rtmsg()
    msg["family"] = AF_INET
    msg["table"] = DEFAULT_TABLE

    netlink.ipv4_get_routes()

    netlink.put.assert_called_once_with(
        msg=msg,
        msg_type=RTM_GETROUTE,
        msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP,
    )


def test_ipv6_get_routes(netlink: Netlink) -> None:
    msg = rtmsg()
    msg["family"] = AF_INET6
    msg["table"] = DEFAULT_TABLE

    netlink.ipv6_get_routes()

    netlink.put.assert_called_once_with(
        msg=msg,
        msg_type=RTM_GETROUTE,
        msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP,
    )


@pytest.mark.parametrize(
    ("network", "gateway"),
    (
        (Network(0x68_B9_1D_DC, 0xFFFFFFFF), "104.185.29.1"),
        (Network(0x14_54_27_00, 0xFFFFFF00), "20.84.39.1"),
        (Network(0xC7_17_00_00, 0xFFFF0000), "199.23.0.1"),
        (Network(0x77_00_00_00, 0xFF000000), "119.0.0.1"),
    ),
)
def test_ipv4_add_route(netlink: Netlink, network: Network, gateway: IPAddress) -> None:
    msg = rtmsg()
    msg["family"] = AF_INET
    msg["table"] = DEFAULT_TABLE
    msg["proto"] = rt_proto["static"]
    msg["type"] = rt_type["unicast"]
    msg["dst_len"] = ipv4_netmask_to_network_size(network.mask)
    msg["attrs"] = [
        ("RTA_TABLE", DEFAULT_TABLE),
        ("RTA_DST", ipv4_int_to_str(network.address)),
        ("RTA_GATEWAY", gateway),
    ]

    netlink.ipv4_add_route(network, gateway)

    netlink.put.assert_called_once_with(
        msg=msg,
        msg_type=RTM_NEWROUTE,
        msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_REPLACE,
    )


@pytest.mark.parametrize(
    ("network", "gateway"),
    (
        (
            Network(0x2A03_2880_F145_0082_FACE_B00C_0000_25DE, 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF),
            "2a03:2880:f145:82:face:b00c:0:1",
        ),
        (
            Network(0x2A00_1450_4005_0800_0000_0000_0000_0000, 0xFFFF_FFFF_FFFF_FF00_0000_0000_0000_0000),
            "2a00:1450:4005:800::1",
        ),
        (
            Network(0x2603_1030_0000_0000_0000_0000_0000_0000, 0xFFFF_FFFF_0000_0000_0000_0000_0000_0000),
            "2603:1030::1",
        ),
    ),
)
def test_ipv6_add_route(netlink: Netlink, network: Network, gateway: IPAddress) -> None:
    msg = rtmsg()
    msg["family"] = AF_INET6
    msg["table"] = DEFAULT_TABLE
    msg["proto"] = rt_proto["static"]
    msg["type"] = rt_type["unicast"]
    msg["dst_len"] = ipv6_netmask_to_network_size(network.mask)
    msg["attrs"] = [
        ("RTA_TABLE", DEFAULT_TABLE),
        ("RTA_DST", ipv6_int_to_str(network.address)),
        ("RTA_GATEWAY", gateway),
    ]

    netlink.ipv6_add_route(network, gateway)

    netlink.put.assert_called_once_with(
        msg=msg,
        msg_type=RTM_NEWROUTE,
        msg_flags=NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_REPLACE,
    )


@pytest.mark.parametrize(
    ("network", "gateway"),
    (
        (Network(0x68_B9_1D_DC, 0xFFFFFFFF), "104.185.29.1"),
        (Network(0x14_54_27_00, 0xFFFFFF00), "20.84.39.1"),
        (Network(0xC7_17_00_00, 0xFFFF0000), "199.23.0.1"),
        (Network(0x77_00_00_00, 0xFF000000), "119.0.0.1"),
    ),
)
def test_ipv4_del_route(netlink: Netlink, network: Network, gateway: IPAddress) -> None:
    msg = rtmsg()
    msg["family"] = AF_INET
    msg["table"] = DEFAULT_TABLE
    msg["proto"] = rt_proto["static"]
    msg["type"] = rt_type["unicast"]
    msg["dst_len"] = ipv4_netmask_to_network_size(network.mask)
    msg["attrs"] = [
        ("RTA_TABLE", DEFAULT_TABLE),
        ("RTA_DST", ipv4_int_to_str(network.address)),
        ("RTA_GATEWAY", gateway),
    ]

    netlink.ipv4_del_route(network, gateway)

    netlink.put.assert_called_once_with(
        msg=msg,
        msg_type=RTM_DELROUTE,
        msg_flags=NLM_F_REQUEST | NLM_F_ACK,
    )


@pytest.mark.parametrize(
    ("network", "gateway"),
    (
        (
            Network(0x2A03_2880_F145_0082_FACE_B00C_0000_25DE, 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF),
            "2a03:2880:f145:82:face:b00c:0:1",
        ),
        (
            Network(0x2A00_1450_4005_0800_0000_0000_0000_0000, 0xFFFF_FFFF_FFFF_FF00_0000_0000_0000_0000),
            "2a00:1450:4005:800::1",
        ),
        (
            Network(0x2603_1030_0000_0000_0000_0000_0000_0000, 0xFFFF_FFFF_0000_0000_0000_0000_0000_0000),
            "2603:1030::1",
        ),
    ),
)
def test_ipv6_del_route(netlink: Netlink, network: Network, gateway: IPAddress) -> None:
    msg = rtmsg()
    msg["family"] = AF_INET6
    msg["table"] = DEFAULT_TABLE
    msg["proto"] = rt_proto["static"]
    msg["type"] = rt_type["unicast"]
    msg["dst_len"] = ipv6_netmask_to_network_size(network.mask)
    msg["attrs"] = [
        ("RTA_TABLE", DEFAULT_TABLE),
        ("RTA_DST", ipv6_int_to_str(network.address)),
        ("RTA_GATEWAY", gateway),
    ]

    netlink.ipv6_del_route(network, gateway)

    netlink.put.assert_called_once_with(
        msg=msg,
        msg_type=RTM_DELROUTE,
        msg_flags=NLM_F_REQUEST | NLM_F_ACK,
    )
