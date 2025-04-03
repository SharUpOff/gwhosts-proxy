from enum import Enum
from socket import AF_INET, AF_INET6
from typing import NamedTuple

from ..dns import DNSData
from ..network import Address


class RTMEvent(Enum):
    NEW_ROUTE: str = "RTM_NEWROUTE"
    DEL_ROUTE: str = "RTM_DELROUTE"
    GET_ROUTE: str = "RTM_GETROUTE"
    NEW_LINK: str = "RTM_NEWLINK"


class LinkState(Enum):
    UP: str = "up"
    DOWN: str = "down"


class AddressFamily(Enum):
    AF_INET: int = AF_INET
    AF_INET6: int = AF_INET6


class DNSDataMessage(NamedTuple):
    data: DNSData
    address: Address
