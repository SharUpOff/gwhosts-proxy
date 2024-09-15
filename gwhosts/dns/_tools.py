from gwhosts.dns._types import DNSData, RRType, Header


def remove_ipv6(data: DNSData) -> DNSData:
    answers = [answer for answer in data.answers if answer.rr_type != RRType.AAAA.value]
    header = data.header

    return DNSData(
        header=Header(
            id=header.id,
            flags=header.flags,
            questions=header.questions,
            answers=len(answers),
            authorities=header.authorities,
            additions=header.additions,
        ),
        questions=data.questions,
        answers=answers,
        authorities=data.authorities,
        additions=data.additions,
    )
