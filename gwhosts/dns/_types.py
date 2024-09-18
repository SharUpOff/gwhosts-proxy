from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class Flags(Enum):
    """DNS Header Flags Masks
    :param AA: Authoritative Answer [https://www.iana.org/go/rfc1035]
    :param TC: Truncated Response [https://www.iana.org/go/rfc1035]
    :param RD: Recursion Desired [https://www.iana.org/go/rfc1035]
    :param RA: Recursion Available [https://www.iana.org/go/rfc1035]
    :see: https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml#dns-parameters-12
    """

    QR: int = 0b10000000_00000000
    OPCODE: int = 0b01111000_00000000
    AA: int = 0b00000100_00000000
    TC: int = 0b00000010_00000000
    RD: int = 0b00000001_00000000
    RA: int = 0b00000000_10000000
    Z: int = 0b00000000_01110000
    RCODE: int = 0b00000000_00001111


class DNSClass(Enum):
    """DNS CLASSes
    :param IN: Internet (IN) [https://www.iana.org/go/rfc1035]
    :see: https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml#dns-parameters-2
    """

    IN: int = 1


class RRType(Enum):
    """Resource Record (RR) TYPEs
    :param A: IPv4 Address [https://www.iana.org/go/rfc1035]
    :param AAAA: IPv6 Address [https://www.iana.org/go/rfc3596]
    :param CNAME: the canonical name for an alias [https://www.iana.org/go/rfc1035]
    :see: https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml#dns-parameters-4
    """

    A: int = 1
    AAAA: int = 28
    CNAME: int = 5


@dataclass
class Header:
    id: int
    flags: int
    questions: int
    answers: int
    authorities: int
    additions: int

    @property
    def qr(self) -> bool:
        return bool(self.flags & Flags.QR.value)

    @property
    def aa(self) -> bool:
        return bool(self.flags & Flags.AA.value)


class QName(Tuple[bytes]):
    pass


@dataclass
class Question:
    """
    :param name: Name of the requested resource
    :param rr_type: Type of RR (A, AAAA, MX, TXT, etc.)
    :param rr_class: Class code
    """

    name: QName
    rr_type: RRType
    rr_class: int


@dataclass
class _RR(Question):
    """Resource Record (RR)
    :param ttl: Count of seconds that the RR stays valid (The maximum is 2^31−1, which is about 68 years)
    :param rr_data_length: Length of rr_data field (specified in octets)
    :param rr_data: Additional RR-specific data
    """

    ttl: int
    rr_data_length: int
    rr_data: bytes


class Answer(_RR):
    pass


class Authority(_RR):
    pass


class Addition(_RR):
    pass


@dataclass
class DNSData:
    header: Header
    questions: List[Question]
    answers: List[Answer]
    authorities: List[Authority]
    additions: List[Addition]
