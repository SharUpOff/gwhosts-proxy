import pytest

from gwhosts.dns import DNSData, Header, Question, Addition, QName, Answer, RRType, serialize


@pytest.mark.parametrize(
    ("dto", "raw"),
    (
        (
            DNSData(
                header=Header(id=44458, flags=0b10000001_10000000, questions=1, answers=5, authorities=0, additions=1),
                questions=[
                    Question(name=QName((b"www", b"youtube", b"com")), rr_type=RRType.AAAA.value, rr_class=1),
                ],
                answers=[
                    Answer(
                        name=QName((b"www", b"youtube", b"com")),
                        rr_type=RRType.CNAME.value,
                        rr_class=1,
                        ttl=810,
                        rr_data_length=22,
                        rr_data=b"\x0ayoutube-ui\x01l\x06google\xc0\x18",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.AAAA.value,
                        rr_class=1,
                        ttl=810,
                        rr_data_length=16,
                        rr_data=b"\x2a\x00\x14\x50\x40\x05\x08\x0b\x00\x00\x00\x00\x00\x00\x20\x0e",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.AAAA.value,
                        rr_class=1,
                        ttl=810,
                        rr_data_length=16,
                        rr_data=b"\x2a\x00\x14\x50\x40\x05\x08\x02\x00\x00\x00\x00\x00\x00\x20\x0e",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.AAAA.value,
                        rr_class=1,
                        ttl=810,
                        rr_data_length=16,
                        rr_data=b"\x2a\x00\x14\x50\x40\x05\x08\x00\x00\x00\x00\x00\x00\x00\x20\x0e",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.AAAA.value,
                        rr_class=1,
                        ttl=810,
                        rr_data_length=16,
                        rr_data=b"\x2a\x00\x14\x50\x40\x05\x08\x01\x00\x00\x00\x00\x00\x00\x20\x0e",
                    ),
                ],
                authorities=[],
                additions=[
                    Addition(
                        name=QName(), rr_type=RRType.OPT.value, rr_class=65494, ttl=0, rr_data_length=0, rr_data=b""
                    ),
                ],
            ),
            b"\xad\xaa\x81\x80\x00\x01\x00\x05\x00\x00\x00\x01\x03\x77\x77\x77\x07\x79\x6f\x75\x74\x75\x62\x65\x03\x63\x6f"
            b"\x6d\x00\x00\x1c\x00\x01\x03\x77\x77\x77\x07\x79\x6f\x75\x74\x75\x62\x65\x03\x63\x6f\x6d\x00\x00\x05\x00\x01"
            b"\x00\x00\x03\x2a\x00\x16\x0a\x79\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\xc0"
            b"\x18\x0a\x79\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00"
            b"\x1c\x00\x01\x00\x00\x03\x2a\x00\x10\x2a\x00\x14\x50\x40\x05\x08\x0b\x00\x00\x00\x00\x00\x00\x20\x0e\x0a\x79"
            b"\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00\x1c\x00\x01"
            b"\x00\x00\x03\x2a\x00\x10\x2a\x00\x14\x50\x40\x05\x08\x02\x00\x00\x00\x00\x00\x00\x20\x0e\x0a\x79\x6f\x75\x74"
            b"\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00\x1c\x00\x01\x00\x00\x03"
            b"\x2a\x00\x10\x2a\x00\x14\x50\x40\x05\x08\x00\x00\x00\x00\x00\x00\x00\x20\x0e\x0a\x79\x6f\x75\x74\x75\x62\x65"
            b"\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00\x1c\x00\x01\x00\x00\x03\x2a\x00\x10"
            b"\x2a\x00\x14\x50\x40\x05\x08\x01\x00\x00\x00\x00\x00\x00\x20\x0e\x00\x00\x29\xff\xd6\x00\x00\x00\x00\x00\x00",
        ),
        (
            DNSData(
                header=Header(id=26706, flags=0b10000001_10000000, questions=1, answers=5, authorities=0, additions=1),
                questions=[
                    Question(name=QName((b"www", b"youtube", b"com")), rr_type=RRType.A.value, rr_class=1),
                ],
                answers=[
                    Answer(
                        name=QName((b"www", b"youtube", b"com")),
                        rr_type=RRType.CNAME.value,
                        rr_class=1,
                        ttl=1933,
                        rr_data_length=22,
                        rr_data=b"\x0ayoutube-ui\x01l\x06google\xc0\x18",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.A.value,
                        rr_class=1,
                        ttl=1933,
                        rr_data_length=4,
                        rr_data=b"\xac\xd9\x13\x4e",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.A.value,
                        rr_class=1,
                        ttl=1933,
                        rr_data_length=4,
                        rr_data=b"\xac\xd9\x10\x4e",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.A.value,
                        rr_class=1,
                        ttl=1933,
                        rr_data_length=4,
                        rr_data=b"\x8e\xfa\xb5\xce",
                    ),
                    Answer(
                        name=QName((b"youtube-ui", b"l", b"google", b"com")),
                        rr_type=RRType.A.value,
                        rr_class=1,
                        ttl=1933,
                        rr_data_length=4,
                        rr_data=b"\x8e\xfb\xd1\x8e",
                    ),
                ],
                authorities=[],
                additions=[
                    Addition(
                        name=QName(), rr_type=RRType.OPT.value, rr_class=65494, ttl=0, rr_data_length=0, rr_data=b""
                    ),
                ],
            ),
            b"\x68\x52\x81\x80\x00\x01\x00\x05\x00\x00\x00\x01\x03\x77\x77\x77\x07\x79\x6f\x75\x74\x75\x62\x65\x03\x63\x6f"
            b"\x6d\x00\x00\x01\x00\x01\x03\x77\x77\x77\x07\x79\x6f\x75\x74\x75\x62\x65\x03\x63\x6f\x6d\x00\x00\x05\x00\x01"
            b"\x00\x00\x07\x8d\x00\x16\x0a\x79\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\xc0"
            b"\x18\x0a\x79\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00"
            b"\x01\x00\x01\x00\x00\x07\x8d\x00\x04\xac\xd9\x13\x4e\x0a\x79\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06"
            b"\x67\x6f\x6f\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00\x01\x00\x01\x00\x00\x07\x8d\x00\x04\xac\xd9\x10\x4e\x0a\x79"
            b"\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00\x01\x00\x01"
            b"\x00\x00\x07\x8d\x00\x04\x8e\xfa\xb5\xce\x0a\x79\x6f\x75\x74\x75\x62\x65\x2d\x75\x69\x01\x6c\x06\x67\x6f\x6f"
            b"\x67\x6c\x65\x03\x63\x6f\x6d\x00\x00\x01\x00\x01\x00\x00\x07\x8d\x00\x04\x8e\xfb\xd1\x8e\x00\x00\x29\xff\xd6"
            b"\x00\x00\x00\x00\x00\x00",
        ),
    ),
)
def test_serialize(raw: bytes, dto: DNSData) -> None:
    assert serialize(dto) == raw