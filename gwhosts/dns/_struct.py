from struct import unpack, error, calcsize
from typing import Any, BinaryIO, Tuple

from ._exceptions import DNSParserUnpackError


def unpack_bytes(fmt: str, buffer: bytes) -> Tuple[Any, ...]:
    try:
        return unpack(fmt, buffer)

    except error as e:
        raise DNSParserUnpackError from e


def unpack_buffer(fmt: str, buffer: BinaryIO) -> Tuple[Any, ...]:
    return unpack_bytes(fmt, buffer.read(calcsize(fmt)))
