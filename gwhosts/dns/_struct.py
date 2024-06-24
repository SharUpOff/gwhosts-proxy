import struct
from gwhosts.dns._exceptions import DNSParserError


def unpack(*args, **kwargs):
    try:
        return struct.unpack(*args, **kwargs)

    except struct.error as e:
        raise DNSParserError from e
