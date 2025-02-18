import pytest
from gwhosts.dns import Answer, QName, RRType, answer_to_str


@pytest.mark.parametrize(
    ("answer", "string"),
    (
        (
            Answer(
                name=QName((b"www", b"youtube", b"com")),
                rr_type=RRType.CNAME.value,
                rr_class=1,
                ttl=810,
                rr_data_length=22,
                rr_data=QName((b"youtube-ui", b"l", b"google", b"com")),
            ),
            "www.youtube.com -> youtube-ui.l.google.com",
        ),
        (
            Answer(
                name=QName((b"youtube-ui", b"l", b"google", b"com")),
                rr_type=RRType.A.value,
                rr_class=1,
                ttl=1933,
                rr_data_length=4,
                rr_data=b"\xac\xd9\x13\x4e",
            ),
            "youtube-ui.l.google.com -> 172.217.19.78",
        ),
        (
            Answer(
                name=QName((b"youtube-ui", b"l", b"google", b"com")),
                rr_type=RRType.AAAA.value,
                rr_class=1,
                ttl=810,
                rr_data_length=16,
                rr_data=b"\x2a\x00\x14\x50\x40\x05\x08\x0b\x00\x00\x00\x00\x00\x00\x20\x0e",
            ),
            "youtube-ui.l.google.com -> 2a00:1450:4005:80b::200e",
        ),
        (
            Answer(
                name=QName((b"youtube-ui", b"l", b"google", b"com")),
                rr_type=RRType.OPT.value,
                rr_class=1,
                ttl=810,
                rr_data_length=16,
                rr_data=b"\x75\x6e\x6b\x6e\x6f\x77\x6e",
            ),
            "youtube-ui.l.google.com -> b'unknown'",
        ),
    ),
)
def test_answer_to_str(answer: Answer, string: str) -> None:
    assert answer_to_str(answer) == string
