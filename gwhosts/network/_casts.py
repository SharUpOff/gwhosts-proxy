from socket import inet_aton, inet_ntoa
from struct import pack, unpack
from typing import Iterable, Iterator

from gwhosts.network._types import IPAddress, IPBinary, Network, NetworkSize, RouteClass

NETSIZE_MAX = 32
NETMASK_MAX: IPBinary = 0xFFFFFFFF
NETMASK_MIN: IPBinary = 0xFF000000

# all normal routes are put there by default
# https://www.kernel.org/doc/Documentation/networking/policy-routing.txt
RT_CLASS_MAIN: RouteClass = 254


def ipv4_bytes_to_int(address: bytes) -> IPBinary:
    return unpack("!L", address)[0]


def ipv4_str_to_int(address: IPAddress) -> IPBinary:
    return unpack("!L", inet_aton(address))[0]


def ipv4_int_to_str(number: IPBinary) -> IPAddress:
    return inet_ntoa(pack("!L", number))


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


def reduce_subnets(addresses: Iterable[Network]) -> Iterator[Network]:
    addresses = sorted(addresses)
    length = len(addresses)
    idx = 0

    while idx < length:
        netaddr, netmask = addresses[idx].address, addresses[idx].mask

        _netmask = netmask
        _netaddr = netaddr & _netmask

        idx += 1

        while idx < length:
            _address = addresses[idx].address

            while _netmask ^ NETMASK_MIN:
                if _address & _netmask == _netaddr:
                    netaddr, netmask = _netaddr, _netmask
                    break

                _netmask &= _netmask << 8
                _netaddr &= _netmask

            else:
                break

            _netaddr, _netmask = netaddr, netmask

            idx += 1

        yield Network(
            address=netaddr,
            mask=netmask,
        )
