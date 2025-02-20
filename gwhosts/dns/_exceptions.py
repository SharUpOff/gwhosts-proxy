class DNSException(Exception):
    pass


class DNSParserError(DNSException):
    pass


class DNSParserUnpackError(DNSParserError):
    pass


class DNSParserRecursionError(DNSParserError):
    pass


class DNSParserInvalidLabelLengthError(DNSParserError):
    pass
