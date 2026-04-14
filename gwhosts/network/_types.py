from socket import AF_INET, SOCK_DGRAM, socket
from typing import Any, NamedTuple, Optional

RouteClass = int
IPAddress = str
Port = int
NetworkSize = int
IPBinary = int

# all normal routes are put there by default
# https://www.kernel.org/doc/Documentation/networking/policy-routing.txt
RT_CLASS_MAIN: RouteClass = 254


class Address(NamedTuple):
    host: IPAddress
    port: Port


class ExpiringAddress(NamedTuple):
    address: Address
    time: float


class Datagram(NamedTuple):
    data: bytes
    target: Address


class Network(NamedTuple):
    address: IPBinary
    mask: IPBinary


class GatewayInfo(NamedTuple):
    address: Optional[IPAddress]
    ifname: Optional[str]


class UDPSocket(socket):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(AF_INET, SOCK_DGRAM, *args, **kwargs)
