from io import BytesIO
from typing import BinaryIO, Iterable, Tuple, Union

from ._exceptions import DNSParserRecursionError
from ._struct import unpack_bytes, unpack_buffer
from ._types import Addition, Answer, Authority, DNSData, Header, QName, Question, RRType

# [https://www.rfc-editor.org/rfc/rfc1035.html#section-2.3.4]
_MAX_DOMAIN_NAME_WIRE_OCTETS: int = 255
_MAX_COMPRESSION_POINTERS: int = (_MAX_DOMAIN_NAME_WIRE_OCTETS + 1) // 2 - 2


def _parse_header(buffer: BinaryIO) -> Header:
    return Header(*unpack_buffer("!HHHHHH", buffer))


def _parse_compressed_name(length: int, buffer: BinaryIO, depth: int) -> Iterable[bytes]:
    pointer_bytes = bytes([length & 0b0011_1111]) + buffer.read(1)
    pointer = unpack_bytes("!H", pointer_bytes)[0]
    current_pos = buffer.tell()
    buffer.seek(pointer)
    for name in _parse_name(buffer, depth):
        yield name

    buffer.seek(current_pos)


def _parse_name(buffer: BinaryIO, depth: int) -> Iterable[bytes]:
    while (length := (buffer.read(1) or b"\0x00")[0]) != 0:
        if length & 0b1100_0000:
            if depth > _MAX_COMPRESSION_POINTERS:
                raise DNSParserRecursionError(f"The limit of {_MAX_COMPRESSION_POINTERS} pointers has been reached")

            for name in _parse_compressed_name(length, buffer, depth + 1):
                yield name

            break

        else:
            yield buffer.read(length)


def _parse_qname(buffer: BinaryIO) -> QName:
    return QName(_parse_name(buffer, 0))


def _parse_question(buffer: BinaryIO) -> Question:
    name = _parse_qname(buffer)
    rr_type, rr_class = unpack_buffer("!HH", buffer)
    return Question(name, rr_type, rr_class)


def _parse_resource(buffer: BinaryIO) -> Tuple[QName, RRType, int, int, int, Union[QName, bytes]]:
    name = _parse_qname(buffer)
    rr_type, rr_class, ttl, rr_data_length = unpack_buffer("!HHIH", buffer)

    if rr_type == RRType.CNAME.value:
        rr_data = _parse_qname(buffer)

    else:
        rr_data = buffer.read(rr_data_length)

    return name, rr_type, rr_class, ttl, rr_data_length, rr_data


def _parse_answer(buffer: BinaryIO) -> Answer:
    return Answer(*_parse_resource(buffer))


def _parse_authority(buffer: BinaryIO) -> Authority:
    return Authority(*_parse_resource(buffer))


def _parse_addition(buffer: BinaryIO) -> Addition:
    return Addition(*_parse_resource(buffer))


def _bytes_to_buffer(data: bytes) -> BytesIO:
    return BytesIO(data)


def _parse(buffer: BytesIO) -> DNSData:
    header = _parse_header(buffer)

    return DNSData(
        header=header,
        questions=[_parse_question(buffer) for _ in range(header.questions)],
        answers=[_parse_answer(buffer) for _ in range(header.answers)],
        authorities=[_parse_authority(buffer) for _ in range(header.authorities)],
        additions=[_parse_addition(buffer) for _ in range(header.additions)],
    )


def parse(data: bytes) -> DNSData:
    return _parse(_bytes_to_buffer(data))
