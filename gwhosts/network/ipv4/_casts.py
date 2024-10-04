from socket import AF_INET, inet_ntop, inet_pton
from struct import pack, unpack

from ._types import IPV4_NETMASK_MAX, IPV4_NETSIZE_MAX
from .._types import IPAddress, IPBinary, Network, NetworkSize


def ipv4_bytes_to_int(address: bytes) -> IPBinary:
    return unpack("!L", address)[0]


def ipv4_int_to_bytes(number: IPBinary) -> bytes:
    return pack("!L", number)


def ipv4_bytes_to_str(address: bytes) -> IPAddress:
    return inet_ntop(AF_INET, address)


def ipv4_str_to_bytes(address: IPAddress) -> bytes:
    return inet_pton(AF_INET, address)


def ipv4_str_to_int(address: IPAddress) -> IPBinary:
    return ipv4_bytes_to_int(ipv4_str_to_bytes(address))


def ipv4_int_to_str(number: IPBinary) -> IPAddress:
    return ipv4_bytes_to_str(ipv4_int_to_bytes(number))


def ipv4_network_to_str(network: Network) -> str:
    return f"{ipv4_int_to_str(network.address)}/{ipv4_netmask_to_network_size(network.mask)}"


def ipv4_str_to_network(address: str) -> Network:
    parts = address.split("/")

    if len(parts) == 1:
        return Network(ipv4_str_to_int(address), IPV4_NETMASK_MAX)

    if len(parts) == 2:
        return Network(ipv4_str_to_int(parts[0]), ipv4_network_size_to_netmask(NetworkSize(parts[1])))

    raise ValueError(f"{address} is not a network address")


def ipv4_netmask_to_network_size(netmask: IPBinary) -> NetworkSize:
    return IPV4_NETSIZE_MAX - (IPV4_NETMASK_MAX ^ netmask).bit_length()


def ipv4_network_size_to_netmask(size: NetworkSize) -> IPBinary:
    return IPV4_NETMASK_MAX >> size ^ IPV4_NETMASK_MAX
