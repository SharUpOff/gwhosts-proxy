from dataclasses import astuple
from struct import pack
from typing import Iterable

from ._types import Addition, Answer, Authority, DNSData, Header, QName, Question


def _encode_qname(qname: Iterable[bytes]) -> bytes:
    return b"".join(bytes([len(part)]) + part for part in qname) + b"\x00"


def _serialize_header(header: Header) -> bytes:
    return pack("!HHHHHH", *astuple(header))


def _serialize_question(question: Question) -> bytes:
    return _encode_qname(question.name) + pack("!HH", question.rr_type, question.rr_class)


def _serialize_resource(
    name: QName,
    rr_type: int,
    rr_class: int,
    ttl: int,
    rr_data_length: int,
    rr_data: bytes,
) -> bytes:
    return _encode_qname(name) + pack("!HHIH", rr_type, rr_class, ttl, rr_data_length) + rr_data


def _serialize_answer(answer: Answer) -> bytes:
    return _serialize_resource(*astuple(answer))


def _serialize_authority(authority: Authority) -> bytes:
    return _serialize_resource(*astuple(authority))


def _serialize_addition(addition: Addition) -> bytes:
    return _serialize_resource(*astuple(addition))


def serialize(data: DNSData) -> bytes:
    return b"".join(
        (
            _serialize_header(data.header),
            *[_serialize_question(question) for question in data.questions],
            *[_serialize_answer(answer) for answer in data.answers],
            *[_serialize_authority(authority) for authority in data.authorities],
            *[_serialize_addition(addition) for addition in data.additions],
        )
    )
