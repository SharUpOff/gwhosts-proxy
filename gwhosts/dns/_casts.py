from ._parsers import parse_qname
from ._types import QName, Answer, RRType
from ..network.ipv4 import ipv4_bytes_to_str
from ..network.ipv6 import ipv6_bytes_to_str


def qname_to_str(qname: QName) -> str:
    return b".".join(qname).decode("utf8")


def qname_bytes_to_str(data: bytes) -> str:
    return qname_to_str(parse_qname(data))


_RR_TO_STR = {
    RRType.A.value: ipv4_bytes_to_str,
    RRType.AAAA.value: ipv6_bytes_to_str,
    RRType.CNAME.value: qname_bytes_to_str,
}


def answer_to_str(answer: Answer) -> str:
    if answer.rr_type in _RR_TO_STR:
        return f"{qname_to_str(answer.name)} -> {_RR_TO_STR[answer.rr_type](answer.rr_data)}"

    return f"{qname_to_str(answer.name)} -> {answer.rr_data}"
