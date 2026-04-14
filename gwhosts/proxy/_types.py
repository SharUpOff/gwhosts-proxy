from enum import Enum, IntEnum
from socket import AF_INET, AF_INET6
from typing import NamedTuple

from ..dns import DNSData
from ..network import Address


class RTMEvent(str, Enum):
    NEW_ROUTE = "RTM_NEWROUTE"
    DEL_ROUTE = "RTM_DELROUTE"
    GET_ROUTE = "RTM_GETROUTE"
    NEW_LINK = "RTM_NEWLINK"


class LinkState(str, Enum):
    UP = "up"
    DOWN = "down"


class AddressFamily(IntEnum):
    AF_INET = AF_INET
    AF_INET6 = AF_INET6


class DNSDataMessage(NamedTuple):
    data: DNSData
    address: Address
