from typing import Set, List

import pytest

from gwhosts.network.ipv4 import (
    ipv4_reduce_subnets,
    ipv4_network_to_str,
    ipv4_str_to_network,
)


@pytest.mark.parametrize(
    ("source", "result"),
    (
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
        ),
    ),
)
def test_ipv4_reduce_subnets(source: Set[str], result: Set[str]) -> None:
    assert {
        ipv4_network_to_str(subnet)
        for subnet in ipv4_reduce_subnets(ipv4_str_to_network(address) for address in source)
    } == result


@pytest.mark.parametrize(
    ("source", "result"),
    (
        (
            {"192.168.1.1", "192.168.1.2", "192.168.2.1", "192.168.2.2", "192.1.1.1", "1.1.1.1"},
            ["1.1.1.1/32", "192.1.1.1/32", "192.168.1.1/32", "192.168.1.2/32", "192.168.2.1/32", "192.168.2.2/32"],
        ),
        (
            {"192.168.1.0/24", "192.168.0.0/16"},
            ["192.168.0.0/16", "192.168.1.0/24"],
        ),
    ),
)
def test_ipv4_sort_addresses(source: Set[str], result: List[str]) -> None:
    assert [
        ipv4_network_to_str(network) for network in sorted(ipv4_str_to_network(address) for address in source)
    ] == result
