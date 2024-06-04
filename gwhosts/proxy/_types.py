from enum import Enum
from typing import NamedTuple

from gwhosts.dns import DNSData
from gwhosts.network import Address


class RTMEvent(Enum):
    NEW_ROUTE: str = "RTM_NEWROUTE"
    DEL_ROUTE: str = "RTM_DELROUTE"
    GET_ROUTE: str = "RTM_GETROUTE"


class DNSDataMessage(NamedTuple):
    data: DNSData
    address: Address
