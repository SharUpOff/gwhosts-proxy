from typing import NamedTuple

import pytest

from gwhosts.network import (
    IPAddress,
    IPBinary,
    Network,
    ipv4_bytes_to_int,
    ipv4_int_to_bytes,
    ipv4_bytes_to_str,
    ipv4_str_to_bytes,
    ipv4_str_to_int,
    ipv4_int_to_str,
    ipv6_bytes_to_int,
    ipv6_int_to_bytes,
    ipv6_bytes_to_str,
    ipv6_str_to_bytes,
    ipv6_str_to_int,
    ipv6_int_to_str,
    network_to_str,
    str_to_network,
    netmask_to_network_size,
    network_size_to_netmask,
)


class IPRepr(NamedTuple):
    number: IPBinary
    bytes: bytes
    string: IPAddress


_IPV4_DATA = (
    # randint(0, 2**32-1)
    IPRepr(0xA4BE422F, b"\xa4\xbe\x42\x2f", "164.190.66.47"),
    IPRepr(0xD31623F8, b"\xd3\x16\x23\xf8", "211.22.35.248"),
    IPRepr(0x8B0DBEB7, b"\x8b\x0d\xbe\xb7", "139.13.190.183"),
    IPRepr(0x43BCF1A8, b"\x43\xbc\xf1\xa8", "67.188.241.168"),
    IPRepr(0xDD8C04E5, b"\xdd\x8c\x04\xe5", "221.140.4.229"),
)


@pytest.mark.parametrize(("src", "dst"), ((ip.bytes, ip.number) for ip in _IPV4_DATA))
def test_ipv4_bytes_to_int(src: bytes, dst: IPBinary) -> None:
    assert ipv4_bytes_to_int(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.number, ip.bytes) for ip in _IPV4_DATA))
def test_ipv4_int_to_bytes(src: IPBinary, dst: bytes) -> None:
    assert ipv4_int_to_bytes(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.bytes, ip.string) for ip in _IPV4_DATA))
def test_ipv4_bytes_to_str(src: bytes, dst: IPAddress) -> None:
    assert ipv4_bytes_to_str(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.string, ip.bytes) for ip in _IPV4_DATA))
def test_ipv4_str_to_bytes(src: IPAddress, dst: bytes) -> None:
    assert ipv4_str_to_bytes(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.string, ip.number) for ip in _IPV4_DATA))
def test_ipv4_str_to_int(src: IPAddress, dst: IPBinary) -> None:
    assert ipv4_str_to_int(src) == dst


@pytest.mark.parametrize(("src", "dst"), ((ip.number, ip.string) for ip in _IPV4_DATA))
def test_ipv4_int_to_str(src: IPBinary, dst: IPAddress) -> None:
    assert ipv4_int_to_str(src) == dst


_IPV6_DATA = (
    # randint(0, 2**128-1)
    IPRepr(
        number=0x99D0E578266F31964BD7F557BAF74A6A,
        bytes=b"\x99\xd0\xe5\x78\x26\x6f\x31\x96\x4b\xd7\xf5\x57\xba\xf7\x4a\x6a",
        string="99d0:e578:266f:3196:4bd7:f557:baf7:4a6a",
    ),
    IPRepr(
        number=0xC3D114FB1331538D6DBE2FA6880B7E61,
        bytes=b"\xc3\xd1\x14\xfb\x13\x31\x53\x8d\x6d\xbe\x2f\xa6\x88\x0b\x7e\x61",
        string="c3d1:14fb:1331:538d:6dbe:2fa6:880b:7e61",
    ),
    IPRepr(
        number=0xAC5E73136439DEC7DA0218C77305AFC5,
        bytes=b"\xac\x5e\x73\x13\x64\x39\xde\xc7\xda\x02\x18\xc7\x73\x05\xaf\xc5",
        string="ac5e:7313:6439:dec7:da02:18c7:7305:afc5",
    ),
    IPRepr(
        number=0x9DD8796A043854FD58AED0F3762FB90E,
        bytes=b"\x9d\xd8\x79\x6a\x04\x38\x54\xfd\x58\xae\xd0\xf3\x76\x2f\xb9\x0e",
        string="9dd8:796a:438:54fd:58ae:d0f3:762f:b90e",
    ),
    IPRepr(
        number=0x8EB0476F53B6A7DFD4DE12BEE9C25BDC,
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
    (Network(0x68B91DDC, 0xFFFFFFFF), "104.185.29.220/32"),
    (Network(0x14542700, 0xFFFFFF00), "20.84.39.0/24"),
    (Network(0xC7170000, 0xFFFF0000), "199.23.0.0/16"),
    (Network(0x77000000, 0xFF000000), "119.0.0.0/8"),
)


@pytest.mark.parametrize(("network", "address"), _NETWORK_DATA)
def test_network_to_str(network: Network, address: str) -> None:
    assert network_to_str(network) == address


@pytest.mark.parametrize(("network", "address"), (
    (Network(0x9B6504EF, 0xFFFFFFFF), "155.101.4.239"),
    *_NETWORK_DATA,
))
def test_str_to_network(network: Network, address: str) -> None:
    assert str_to_network(address) == network


@pytest.mark.parametrize("address", (
    "19/09/2024",
    "01/57/AM",
))
def test_not_a_network(address: str) -> None:
    with pytest.raises(ValueError) as cast_error:
        str_to_network(address)

    assert str(cast_error.value) == f"{address} is not a network address"


_NETMASK_DATA = (
    (32, 0xFFFFFFFF),
    (24, 0xFFFFFF00),
    (16, 0xFFFF0000),
    (8, 0xFF000000),
)

@pytest.mark.parametrize(("size", "mask"), _NETMASK_DATA)
def test_netmask_to_network_size(size: int, mask: IPBinary) -> None:
    assert netmask_to_network_size(mask) == size


@pytest.mark.parametrize(("size", "mask"), _NETMASK_DATA)
def test_network_size_to_netmask(size: int, mask: IPBinary) -> None:
    assert network_size_to_netmask(size) == mask
