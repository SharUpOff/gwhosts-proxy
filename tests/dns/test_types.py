import pytest

from gwhosts.dns import Header


@pytest.mark.parametrize(
    ("flags", "qr", "aa", "tc", "rd", "ra"),
    (
        (0b00000000_00000000, False, False, False, False, False),
        (0b10000000_00000000, True, False, False, False, False),
        (0b00000100_00000000, False, True, False, False, False),
        (0b00000010_00000000, False, False, True, False, False),
        (0b00000001_00000000, False, False, False, True, False),
        (0b00000000_10000000, False, False, False, False, True),
        (0b10000111_10000000, True, True, True, True, True),
    ),
)
def test_header_flags(flags: int, qr: bool, aa: bool, tc: bool, rd: bool, ra: bool) -> None:
    header = Header(
        id=0,
        flags=flags,
        questions=0,
        answers=0,
        authorities=0,
        additions=0,
    )
    assert header.qr == qr
    assert header.aa == aa
    assert header.tc == tc
    assert header.rd == rd
    assert header.ra == ra
