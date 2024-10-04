from typing import NamedTuple
from .._types import Port


IPv6String = str
IPv6NetworkSize = int
IPv6Binary = int


IPV6_NETSIZE_MAX: IPv6NetworkSize = 128
IPV6_NETMASK_MAX: IPv6Binary = 0xFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF
IPV6_NETMASK_MIN: IPv6Binary = 0xFFFF_FFFF_0000_0000_0000_0000_0000_0000


class IPv6Address(NamedTuple):
    host: IPv6String
    port: Port


class IPv6ExpiringAddress(NamedTuple):
    address: IPv6Address
    time: float


class IPv6Datagram(NamedTuple):
    data: bytes
    target: IPv6Address


class IPv6Network(NamedTuple):
    address: IPv6Binary
    mask: IPv6Binary
