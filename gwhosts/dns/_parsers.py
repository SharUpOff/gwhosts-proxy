from io import BytesIO
from typing import BinaryIO, Iterable, Tuple

from gwhosts.dns._struct import unpack
from gwhosts.dns._types import Addition, Answer, Authority, DNSData, Header, QName, Question


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
    while (length := (buffer.read(1) or b'\0x00')[0]) != 0:
        if length & 0b1100_0000:
            for name in _parse_compressed_name(length, buffer):
                yield name
            break

        else:
            yield buffer.read(length)


def _parse_qname(buffer: BinaryIO) -> QName:
    return QName(_parse_name(buffer))


def _parse_question(buffer: BinaryIO) -> Question:
    name = _parse_qname(buffer)
    rr_type, rr_class = unpack("!HH", buffer.read(4))
    return Question(name, rr_type, rr_class)


def _parse_resource(buffer: BinaryIO) -> Tuple[QName, int, int, int, int, bytes]:
    name = _parse_qname(buffer)
    rr_type, rr_class, ttl, rr_data_length = unpack("!HHIH", buffer.read(10))
    return name, rr_type, rr_class, ttl, rr_data_length, buffer.read(rr_data_length)


def _parse_answer(buffer: BinaryIO) -> Answer:
    return Answer(*_parse_resource(buffer))


def _parse_authority(buffer: BinaryIO) -> Authority:
    return Authority(*_parse_resource(buffer))


def _parse_addition(buffer: BinaryIO) -> Addition:
    return Addition(*_parse_resource(buffer))


def parse(data: bytes) -> DNSData:
    buffer = BytesIO(data)
    header = _parse_header(buffer)

    return DNSData(
        header=header,
        questions=[_parse_question(buffer) for _ in range(header.questions)],
        answers=[_parse_answer(buffer) for _ in range(header.answers)],
        authorities=[_parse_authority(buffer) for _ in range(header.authorities)],
        additions=[_parse_addition(buffer) for _ in range(header.additions)],
    )
