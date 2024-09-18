from typing import Iterable, Iterator

from gwhosts.network._types import Network, NETMASK_MIN


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
