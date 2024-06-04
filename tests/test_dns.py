import pytest

from gwhosts.dns import (
    DNSData,
    RRType,
    Header,
    Question,
    Answer,
    parse,
    serialize,
)


parameters = (
    (
        b"e\x03\x85\x80\x00\x01\x00\x03\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00"
        b"\x01\x00\x00\x00\x00\x00\x04@\xe9\xa4d\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x00\x00\x04@\xe9\xa4\x8b\xc0"
        b"\x0c\x00\x01\x00\x01\x00\x00\x00\x00\x00\x04@\xe9\xa4\x8a",
        DNSData(
            header=Header(
                id=25859,
                flags=0b10000101_10000000,
                questions=1,
                answers=3,
                authorities=0,
                additions=0,
            ),
            questions=[
                Question(name=(b'google', b'com'), rr_type=1, rr_class=1),
            ],
            answers=[
                Answer(name=(b'google', b'com'), rr_type=1, rr_class=1, ttl=0, rr_data_length=4, rr_data=b'@\xe9\xa4d'),
                Answer(name=(b'google', b'com'), rr_type=1, rr_class=1, ttl=0, rr_data_length=4, rr_data=b'@\xe9\xa4\x8b'),
                Answer(name=(b'google', b'com'), rr_type=1, rr_class=1, ttl=0, rr_data_length=4, rr_data=b'@\xe9\xa4\x8a'),
            ],
            authorities=[],
            additions=[],
        ),
    ),
)


@pytest.mark.parametrize(("raw", "dto"), parameters)
def test_parse(raw: bytes, dto: DNSData) -> None:
    assert parse(raw) == dto


@pytest.mark.parametrize(("raw", "dto"), parameters)
def test_serialize(raw: bytes, dto: DNSData) -> None:
    assert serialize(dto) == raw
