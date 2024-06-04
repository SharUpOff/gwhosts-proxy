from socket import AF_INET, SOCK_DGRAM
from typing import Set, List

import pytest

from gwhosts.network import (
    ipv4_str_to_int,
    ipv4_int_to_str,
    reduce_subnets,
    Network,
    UDPSocket,
    IPAddress,
    IPBinary,
    network_size_to_netmask,
    network_to_str,
    str_to_network,
)


@pytest.mark.parametrize(("network", "string"), (
    (Network(address=0xC0A80101, mask=0xFFFFFFFF), "192.168.1.1/32"),
    (Network(address=0xC0A80100, mask=0xFFFFFF00), "192.168.1.0/24"),
    (Network(address=0xC0A80000, mask=0xFFFF0000), "192.168.0.0/16"),
    (Network(address=0xC0000000, mask=0xFF000000), "192.0.0.0/8"),
))
def test_network_to_str(network: Network, string: str) -> None:
    assert network_to_str(network) == string


@pytest.mark.parametrize(("string", "number"), (
    ("192.168.2.2", 0xC0A80202),
    ("192.168.1.1", 0xC0A80101),
    ("192.168.2.1", 0xC0A80201),
    ("172.16.64.10", 0xAC10400A),
))
def test_ip_to_int(string: IPAddress, number) -> None:
    assert number == ipv4_str_to_int(string)


def test_udp_socket() -> None:
    udp_socket = UDPSocket()

    assert udp_socket.type == SOCK_DGRAM
    assert udp_socket.family == AF_INET


@pytest.mark.parametrize(("size", "mask"), (
    (32, 0xFFFFFFFF),
    (24, 0xFFFFFF00),
    (16, 0xFFFF0000),
    (8, 0xFF000000),
))
def test_network_size_to_netmask(size: int, mask: IPBinary) -> None:
    assert network_size_to_netmask(size) == mask


@pytest.mark.parametrize(("number", "string"), (
    (0xC0A80202, "192.168.2.2"),
    (0xC0A80101, "192.168.1.1"),
    (0xC0A80201, "192.168.2.1"),
    (0xAC10400A, "172.16.64.10"),
))
def test_int_to_ip(number: IPBinary, string: IPAddress) -> None:
    assert string == ipv4_int_to_str(number)


@pytest.mark.parametrize(("source", "result"), (
    (
        {"192.168.1.1"},
        {"192.168.1.1/32"},
    ),
    (
        {"192.168.1.1", "192.168.1.2"},
        {"192.168.1.0/24"},
    ),
    (
        {"192.168.1.1", "192.168.1.2", "192.168.2.1", "192.168.2.2"},
        {"192.168.0.0/16"},
    ),
    (
        {"192.168.1.1", "192.168.1.2", "192.168.2.1", "192.168.2.2", "192.1.1.1"},
        {"192.168.0.0/16", "192.1.1.1/32"},
    ),
    (
        {"192.168.1.1", "192.168.1.2", "192.168.2.1", "192.168.2.2", "192.1.1.1", "1.1.1.1"},
        {"192.168.0.0/16", "192.1.1.1/32", "1.1.1.1/32"},
    ),
    (
        {"192.168.0.0/16", "192.168.1.0/24"},
        {"192.168.0.0/16"},
    )
))
def test_reduce_subnets(source: Set[str], result: Set[str]) -> None:
    assert {
        network_to_str(subnet)
        for subnet in reduce_subnets(
            str_to_network(address)
            for address in source
        )
    } == result


@pytest.mark.parametrize(("source", "result"), (
    (
        {"192.168.1.1", "192.168.1.2", "192.168.2.1", "192.168.2.2", "192.1.1.1", "1.1.1.1"},
        ['1.1.1.1/32', '192.1.1.1/32', '192.168.1.1/32', '192.168.1.2/32', '192.168.2.1/32', '192.168.2.2/32'],
    ),
    (
        {"192.168.1.0/24", "192.168.0.0/16"},
        ["192.168.0.0/16", "192.168.1.0/24"],
    ),
))
def test_sort_addresses(source: Set[str], result: List[str]) -> None:
    assert [network_to_str(network) for network in sorted(str_to_network(address) for address in source)] == result
