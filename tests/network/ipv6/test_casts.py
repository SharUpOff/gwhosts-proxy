from typing import NamedTuple

import pytest

from gwhosts.network import (
    IPAddress,
    IPBinary,
    Network,
)
from gwhosts.network.ipv6 import (
    ipv6_bytes_to_int,
    ipv6_int_to_bytes,
    ipv6_bytes_to_str,
    ipv6_str_to_bytes,
    ipv6_str_to_int,
    ipv6_int_to_str,
    ipv6_network_to_str,
    ipv6_str_to_network,
    ipv6_netmask_to_network_size,
    ipv6_network_size_to_netmask,
)


class IPRepr(NamedTuple):
    number: IPBinary
    bytes: bytes
    string: IPAddress


_IPV6_DATA = (
    # randint(0, 2**128-1)
    IPRepr(
        number=0x99D0_E578_266F_3196_4BD7_F557_BAF7_4A6A,
        bytes=b"\x99\xd0\xe5\x78\x26\x6f\x31\x96\x4b\xd7\xf5\x57\xba\xf7\x4a\x6a",
        string="99d0:e578:266f:3196:4bd7:f557:baf7:4a6a",
    ),
    IPRepr(
        number=0xC3D1_14FB_1331_538D_6DBE_2FA6_880B_7E61,
        bytes=b"\xc3\xd1\x14\xfb\x13\x31\x53\x8d\x6d\xbe\x2f\xa6\x88\x0b\x7e\x61",
        string="c3d1:14fb:1331:538d:6dbe:2fa6:880b:7e61",
    ),
    IPRepr(
        number=0xAC5E_7313_6439_DEC7_DA02_18C7_7305_AFC5,
        bytes=b"\xac\x5e\x73\x13\x64\x39\xde\xc7\xda\x02\x18\xc7\x73\x05\xaf\xc5",
        string="ac5e:7313:6439:dec7:da02:18c7:7305:afc5",
    ),
    IPRepr(
        number=0x9DD8_796A_0438_54FD_58AE_D0F3_762F_B90E,
        bytes=b"\x9d\xd8\x79\x6a\x04\x38\x54\xfd\x58\xae\xd0\xf3\x76\x2f\xb9\x0e",
        string="9dd8:796a:438:54fd:58ae:d0f3:762f:b90e",
    ),
    IPRepr(
        number=0x8EB0_476F_53B6_A7DF_D4DE_12BE_E9C2_5BDC,
        bytes=b"\x8e\xb0\x47\x6f\x53\xb6\xa7\xdf\xd4\xde\x12\xbe\xe9\xc2\x5b\xdc",
        string="8eb0:476f:53b6:a7df:d4de:12be:e9c2:5bdc",
    ),
)


@pytest.mark.parametrize(("src", "dst"), ((ip.bytes, ip.number) for ip in _IPV6_DATA))
def test_ipv6_bytes_to_int(src: bytes, dst: IPBinary) -> None:
    assert ipv6_bytes_to_int(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.number, ip.bytes) for ip in _IPV6_DATA))
def test_ipv6_int_to_bytes(src: IPBinary, dst: bytes) -> None:
    assert ipv6_int_to_bytes(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.bytes, ip.string) for ip in _IPV6_DATA))
def test_ipv6_bytes_to_str(src: bytes, dst: IPAddress) -> None:
    assert ipv6_bytes_to_str(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.string, ip.bytes) for ip in _IPV6_DATA))
def test_ipv6_str_to_bytes(src: IPAddress, dst: bytes) -> None:
    assert ipv6_str_to_bytes(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.string, ip.number) for ip in _IPV6_DATA))
def test_ipv6_str_to_int(src: IPAddress, dst: IPBinary) -> None:
    assert ipv6_str_to_int(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.number, ip.string) for ip in _IPV6_DATA))
def test_ipv6_int_to_str(src: IPBinary, dst: IPAddress) -> None:
    assert ipv6_int_to_str(src) == dst


_NETWORK_DATA = (
    (
        Network(0x2A03_2880_F145_0082_FACE_B00C_0000_25DE, 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF),
        "2a03:2880:f145:82:face:b00c:0:25de/128",
    ),
    (
        Network(0x2A00_1450_4005_0800_0000_0000_0000_0000, 0xFFFF_FFFF_FFFF_FF00_0000_0000_0000_0000),
        "2a00:1450:4005:800::/56",
    ),
    (
        Network(0x2603_1030_0000_0000_0000_0000_0000_0000, 0xFFFF_FFFF_0000_0000_0000_0000_0000_0000),
        "2603:1030::/32",
    ),
)


@pytest.mark.parametrize(("network", "address"), _NETWORK_DATA)
def test_ipv6_network_to_str(network: Network, address: str) -> None:
    assert ipv6_network_to_str(network) == address


@pytest.mark.parametrize(
    ("network", "address"),
    (
        (
            Network(0x99D0_E578_266F_3196_4BD7_F557_BAF7_4A6A, 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF),
            "99d0:e578:266f:3196:4bd7:f557:baf7:4a6a",
        ),
        *_NETWORK_DATA,
    ),
)
def test_ipv6_str_to_network(network: Network, address: str) -> None:
    assert ipv6_str_to_network(address) == network


@pytest.mark.parametrize(
    "address",
    (
        "19/09/2024",
        "01/57/AM",
    ),
)
def test_ipv6_not_a_network(address: str) -> None:
    with pytest.raises(ValueError) as cast_error:
        ipv6_str_to_network(address)

    assert str(cast_error.value) == f"{address} is not a network address"


_NETMASK_DATA = (
    (128, 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF),
    (56, 0xFFFF_FFFF_FFFF_FF00_0000_0000_0000_0000),
    (32, 0xFFFF_FFFF_0000_0000_0000_0000_0000_0000),
)


@pytest.mark.parametrize(("size", "mask"), _NETMASK_DATA)
def test_ipv6_netmask_to_network_size(size: int, mask: IPBinary) -> None:
    assert ipv6_netmask_to_network_size(mask) == size


@pytest.mark.parametrize(("size", "mask"), _NETMASK_DATA)
def test_ipv6_network_size_to_netmask(size: int, mask: IPBinary) -> None:
    assert ipv6_network_size_to_netmask(size) == mask
