from socket import AF_INET6, inet_ntop, inet_pton

from ._types import IPV6_NETMASK_MAX, IPV6_NETSIZE_MAX
from .._types import IPAddress, IPBinary, Network, NetworkSize


def ipv6_bytes_to_int(address: bytes) -> IPBinary:
    return int.from_bytes(address, byteorder="big")


def ipv6_int_to_bytes(number: IPBinary) -> bytes:
    return number.to_bytes(16, byteorder="big")


def ipv6_bytes_to_str(address: bytes) -> IPAddress:
    return inet_ntop(AF_INET6, address)


def ipv6_str_to_bytes(address: IPAddress) -> bytes:
    return inet_pton(AF_INET6, address)


def ipv6_str_to_int(address: IPAddress) -> IPBinary:
    return ipv6_bytes_to_int(ipv6_str_to_bytes(address))


def ipv6_int_to_str(number: IPBinary) -> IPAddress:
    return ipv6_bytes_to_str(ipv6_int_to_bytes(number))


def ipv6_network_to_str(network: Network) -> str:
    return f"{ipv6_int_to_str(network.address)}/{ipv6_netmask_to_network_size(network.mask)}"


def ipv6_str_to_network(address: str) -> Network:
    parts = address.split("/")

    if len(parts) == 1:
        return Network(ipv6_str_to_int(address), IPV6_NETMASK_MAX)

    if len(parts) == 2:
        return Network(ipv6_str_to_int(parts[0]), ipv6_network_size_to_netmask(NetworkSize(parts[1])))

    raise ValueError(f"{address} is not a network address")


def ipv6_netmask_to_network_size(netmask: IPBinary) -> NetworkSize:
    return IPV6_NETSIZE_MAX - (IPV6_NETMASK_MAX ^ netmask).bit_length()


def ipv6_network_size_to_netmask(size: NetworkSize) -> IPBinary:
    return IPV6_NETMASK_MAX >> size ^ IPV6_NETMASK_MAX
