from gwhosts.dns._types import DNSData, RRType


def remove_ipv6(data: DNSData) -> DNSData:
    return DNSData(
        header=data.header,
        questions=data.questions,
        answers=[answer for answer in data.answers if answer.rr_type != RRType.AAAA.value],
        authorities=data.authorities,
        additions=data.additions,
    )
