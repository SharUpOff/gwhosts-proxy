from io import BytesIO
from typing import BinaryIO, Iterable, Tuple

from ._exceptions import DNSParserRecursionError
from ._struct import unpack
from ._types import Addition, Answer, Authority, DNSData, Header, QName, Question, RRType


def _parse_header(buffer: BinaryIO) -> Header:
    return Header(*unpack("!HHHHHH", buffer.read(12)))


def _parse_compressed_name(length: int, buffer: BinaryIO) -> Iterable[bytes]:
    pointer_bytes = bytes([length & 0b0011_1111]) + buffer.read(1)
    pointer = unpack("!H", pointer_bytes)[0]
    current_pos = buffer.tell()
    buffer.seek(pointer)
    for name in _parse_name(buffer):
        yield name

    buffer.seek(current_pos)


def _parse_name(buffer: BinaryIO) -> Iterable[bytes]:
    while (length := (buffer.read(1) or b"\0x00")[0]) != 0:
        if length & 0b1100_0000:
            for name in _parse_compressed_name(length, buffer):
                yield name
            break

        else:
            yield buffer.read(length)


def _parse_qname(buffer: BinaryIO) -> QName:
    try:
        name = _parse_name(buffer)

    except RecursionError as e:
        raise DNSParserRecursionError from e

    return QName(name)


def _parse_question(buffer: BinaryIO) -> Question:
    name = _parse_qname(buffer)
    rr_type, rr_class = unpack("!HH", buffer.read(4))
    return Question(name, rr_type, rr_class)


def _parse_resource(buffer: BinaryIO) -> Tuple[QName, RRType, int, int, int, bytes]:
    name = _parse_qname(buffer)
    rr_type, rr_class, ttl, rr_data_length = unpack("!HHIH", buffer.read(10))
    return name, rr_type, rr_class, ttl, rr_data_length, buffer.read(rr_data_length)


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


def parse_qname(data: bytes) -> QName:
    return _parse_qname(_bytes_to_buffer(data))
