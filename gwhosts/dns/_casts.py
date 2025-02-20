from io import BytesIO
from typing import BinaryIO, Iterable

from ._types import Answer, RRType
from ..network.ipv4 import ipv4_bytes_to_str
from ..network.ipv6 import ipv6_bytes_to_str


def _parse_decompressed_name(buffer: BinaryIO) -> Iterable[bytes]:
    while length := buffer.read(1)[0]:
        yield buffer.read(length)


def qname_to_str(qname: Iterable[bytes]) -> str:
    return b".".join(qname).decode("utf8")


def _name_bytes_to_str(data: bytes) -> str:
    return qname_to_str(_parse_decompressed_name(BytesIO(data)))


_RR_TO_STR = {
    RRType.A.value: ipv4_bytes_to_str,
    RRType.AAAA.value: ipv6_bytes_to_str,
    RRType.CNAME.value: _name_bytes_to_str,
}


def answer_to_str(answer: Answer) -> str:
    if answer.rr_type in _RR_TO_STR:
        return f"{qname_to_str(answer.name)} -> {_RR_TO_STR[answer.rr_type](answer.rr_data)}"

    return f"{qname_to_str(answer.name)} -> {answer.rr_data}"
