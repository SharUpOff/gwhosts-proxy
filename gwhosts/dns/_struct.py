import struct

from ._exceptions import DNSParserUnpackError


def unpack(*args, **kwargs):
    try:
        return struct.unpack(*args, **kwargs)

    except struct.error as e:
        raise DNSParserUnpackError from e
