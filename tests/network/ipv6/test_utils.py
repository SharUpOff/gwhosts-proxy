from typing import Set, List

import pytest

from gwhosts.network.ipv6 import (
    ipv6_reduce_subnets,
    ipv6_network_to_str,
    ipv6_str_to_network,
)


@pytest.mark.parametrize(
    ("source", "result"),
    (
        (
            {
                "2a00:1450:4005:801::200e",
                "2a00:1450:4005:80b::200e",
                "2a00:1450:4005:802::200e",
                "2a00:1450:4005:800::200e",
                "2a00:1450:4005:801::200e",
                "2a00:1450:4005:800::2004",
                "2a00:1450:4005:802::2003",
            },
            {"2a00:1450:4005:800::/56"},
        ),
    ),
)
def test_ipv6_reduce_subnets(source: Set[str], result: Set[str]) -> None:
    assert {
        ipv6_network_to_str(subnet)
        for subnet in ipv6_reduce_subnets(ipv6_str_to_network(address) for address in source)
    } == result


@pytest.mark.parametrize(
    ("source", "result"),
    (
        (
            {"2a00:1450:4005:801::200e", "2a00:1450:4005:80b::200e", "2a00:1450:4005:800::2004"},
            ["2a00:1450:4005:800::2004/128", "2a00:1450:4005:801::200e/128", "2a00:1450:4005:80b::200e/128"],
        ),
        (
            {"2a00:1450:4005:800::/56", "2603:1030::/32"},
            ["2603:1030::/32", "2a00:1450:4005:800::/56"],
        ),
    ),
)
def test_ipv6_sort_addresses(source: Set[str], result: List[str]) -> None:
    assert [
        ipv6_network_to_str(network) for network in sorted(ipv6_str_to_network(address) for address in source)
    ] == result
