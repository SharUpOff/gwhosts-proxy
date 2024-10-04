from typing import NamedTuple

import pytest

from gwhosts.network import (
    IPAddress,
    IPBinary,
    Network,
)
from gwhosts.network.ipv4 import (
    ipv4_bytes_to_int,
    ipv4_int_to_bytes,
    ipv4_bytes_to_str,
    ipv4_str_to_bytes,
    ipv4_str_to_int,
    ipv4_int_to_str,
    ipv4_network_to_str,
    ipv4_str_to_network,
    ipv4_netmask_to_network_size,
    ipv4_network_size_to_netmask,
)


class IPRepr(NamedTuple):
    number: IPBinary
    bytes: bytes
    string: IPAddress


_IPV4_DATA = (
    # randint(0, 2**32-1)
    IPRepr(0xA4_BE_42_2F, b"\xa4\xbe\x42\x2f", "164.190.66.47"),
    IPRepr(0xD3_16_23_F8, b"\xd3\x16\x23\xf8", "211.22.35.248"),
    IPRepr(0x8B_0D_BE_B7, b"\x8b\x0d\xbe\xb7", "139.13.190.183"),
    IPRepr(0x43_BC_F1_A8, b"\x43\xbc\xf1\xa8", "67.188.241.168"),
    IPRepr(0xDD_8C_04_E5, b"\xdd\x8c\x04\xe5", "221.140.4.229"),
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


_NETWORK_DATA = (
    (Network(0x68_B9_1D_DC, 0xFFFFFFFF), "104.185.29.220/32"),
    (Network(0x14_54_27_00, 0xFFFFFF00), "20.84.39.0/24"),
    (Network(0xC7_17_00_00, 0xFFFF0000), "199.23.0.0/16"),
    (Network(0x77_00_00_00, 0xFF000000), "119.0.0.0/8"),
)


@pytest.mark.parametrize(("network", "address"), _NETWORK_DATA)
def test_ipv4_network_to_str(network: Network, address: str) -> None:
    assert ipv4_network_to_str(network) == address


@pytest.mark.parametrize(
    ("network", "address"),
    (
        (Network(0x9B_65_04_EF, 0xFFFFFFFF), "155.101.4.239"),
        *_NETWORK_DATA,
    ),
)
def test_ipv4_str_to_network(network: Network, address: str) -> None:
    assert ipv4_str_to_network(address) == network


@pytest.mark.parametrize(
    "address",
    (
        "19/09/2024",
        "01/57/AM",
    ),
)
def test_ipv4_not_a_network(address: str) -> None:
    with pytest.raises(ValueError) as cast_error:
        ipv4_str_to_network(address)

    assert str(cast_error.value) == f"{address} is not a network address"


_NETMASK_DATA = (
    (32, 0xFFFFFFFF),
    (24, 0xFFFFFF00),
    (16, 0xFFFF0000),
    (8, 0xFF000000),
)


@pytest.mark.parametrize(("size", "mask"), _NETMASK_DATA)
def test_ipv4_netmask_to_network_size(size: int, mask: IPBinary) -> None:
    assert ipv4_netmask_to_network_size(mask) == size


@pytest.mark.parametrize(("size", "mask"), _NETMASK_DATA)
def test_ipv4_network_size_to_netmask(size: int, mask: IPBinary) -> None:
    assert ipv4_network_size_to_netmask(size) == mask
