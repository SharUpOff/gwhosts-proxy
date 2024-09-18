from gwhosts.dns._parsers import parse, parse_qname
from gwhosts.dns._serializers import serialize
from gwhosts.dns._exceptions import DNSParserError
from gwhosts.dns._tools import remove_ipv6
from gwhosts.dns._types import Addition, Answer, Authority, DNSData, Header, QName, Question, RRType

__all__ = [
    "DNSData",
    "DNSParserError",
    "Header",
    "Question",
    "QName",
    "Answer",
    "Authority",
    "Addition",
    "RRType",
    "parse",
    "serialize",
    "remove_ipv6",
    "parse_qname",
]
