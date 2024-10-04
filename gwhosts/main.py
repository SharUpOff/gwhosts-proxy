import gzip
import logging
import sys
from argparse import ArgumentParser

from .dns import QName
from .network import Address
from .performance import no_gc
from .proxy import DNSProxy

if __name__ == "__main__":
    parser = ArgumentParser()

    logging_levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    parser.add_argument("gateway", help="Gateway IPv4")
    parser.add_argument("hostsfile", help="Host List", nargs="?")
    parser.add_argument("--host", dest="host", help="Listening address", default="127.0.0.1")
    parser.add_argument("--ipv6-gateway", dest="ipv6_gateway", help="Gateway IPv6", default=None)
    parser.add_argument("--port", dest="port", help="Listening port", default="8053", type=int)
    parser.add_argument("--dns-host", dest="dns_host", help="Remote DNS address", default="127.0.0.1")
    parser.add_argument("--dns-port", dest="dns_port", help="Remote DNS port", default="65053", type=int)
    parser.add_argument("--timeout", dest="timeout", help="DNS queries timeout in seconds", default=5, type=int)
    parser.add_argument(
        "--log-level",
        dest="log_level",
        help="Logging level",
        default="info",
        choices=logging_levels.keys(),
    )
    parser.add_argument("--log-name", dest="log_name", help="Logger name", default="DNS")

    args = parser.parse_args()

    logger = logging.getLogger(args.log_name)
    logger.setLevel(logging_levels[args.log_level])
    logger.addHandler(logging.StreamHandler(sys.stdout))

    if args.hostsfile:
        logger.info(f"DNS: reading hostnames from {args.hostsfile}")

        with gzip.open(args.hostsfile, "r") as hostsfile:
            with no_gc():
                _hostnames = {QName(_name.split(b".")) for _name in hostsfile.read().splitlines()}

        logger.info(f"DNS: {len(_hostnames)} hostnames were added to the proxying list")

    else:
        _hostnames = set()

    proxy = DNSProxy(
        gateway=args.gateway,
        ipv6_gateway=args.ipv6_gateway,
        to_addr=Address(args.dns_host, args.dns_port),
        hostnames=_hostnames,
        logger=logger,
        timeout_in_seconds=args.timeout,
    )
    proxy.listen(Address(args.host, args.port))
