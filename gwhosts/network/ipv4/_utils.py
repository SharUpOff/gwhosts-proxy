from typing import Iterable, Iterator

from ._types import IPV4_NETMASK_MIN
from .._types import Network
from .._utils import _reduce_subnets


def ipv4_reduce_subnets(addresses: Iterable[Network]) -> Iterator[Network]:
    return _reduce_subnets(addresses, IPV4_NETMASK_MIN)
