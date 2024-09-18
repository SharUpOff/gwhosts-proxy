from socket import AF_INET, AF_INET6, inet_ntop, inet_pton
from struct import pack, unpack

from gwhosts.network._types import IPAddress, IPBinary, Network, NetworkSize, NETMASK_MAX, NETSIZE_MAX


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


def network_to_str(network: Network) -> str:
    return f"{ipv4_int_to_str(network.address)}/{netmask_to_network_size(network.mask)}"


def str_to_network(address: str) -> Network:
    parts = address.split("/")

    if len(parts) == 1:
        return Network(ipv4_str_to_int(address), NETMASK_MAX)

    if len(parts) == 2:
        return Network(ipv4_str_to_int(parts[0]), network_size_to_netmask(NetworkSize(parts[1])))

    raise ValueError(f"{address} is not a network address")


def netmask_to_network_size(netmask: IPBinary) -> NetworkSize:
    return NETSIZE_MAX - (NETMASK_MAX ^ netmask).bit_length()


def network_size_to_netmask(size: NetworkSize) -> IPBinary:
    return NETMASK_MAX >> size ^ NETMASK_MAX
