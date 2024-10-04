from typing import NamedTuple
from .._types import Port


IPv4String = str
IPv4NetworkSize = int
IPv4Binary = int


IPV4_NETSIZE_MAX: IPv4NetworkSize = 32
IPV4_NETMASK_MAX: IPv4Binary = 0xFFFFFFFF
IPV4_NETMASK_MIN: IPv4Binary = 0xFF000000


class IPv4Address(NamedTuple):
    host: IPv4String
    port: Port


class IPv4ExpiringAddress(NamedTuple):
    address: IPv4Address
    time: float


class IPv4Datagram(NamedTuple):
    data: bytes
    target: IPv4Address


class IPv4Network(NamedTuple):
    address: IPv4Binary
    mask: IPv4Binary
