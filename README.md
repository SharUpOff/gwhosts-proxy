# gwhosts-proxy
DNS proxy/router for a specified list of hostnames

## How does this app work
1. The service proxies all DNS queries
2. Adds static routes combining similar addresses into subnets
3. Traffic for the list of hostnames goes through the specified gateway (e.g. VPN)

## Installation
  ```bash
  git clone https://github.com/sharupoff/gwhosts-proxy.git
  cd gwhosts-proxy

  # Prepare a gzipped list of hostnames (edit it before)
  gzip --keep gwhosts.example
  
  # Install dependencies
  python -m venv env
  ./env/bin/pip install .
  ```

## Usage
  ```bash
  ./env/bin/python -m gwhosts.main 192.168.2.1 ./gwhosts.example.gz
  ```

## Used resources
- [Introduction to Netlink](https://docs.kernel.org/next/userspace-api/netlink/intro.html)
- [Kernel routing policy](https://www.kernel.org/doc/Documentation/networking/policy-routing.txt)
- [IPRoute module](https://docs.pyroute2.org/iproute.html)
- [Domain Name System (DNS) Parameters](https://www.iana.org/assignments/dns-parameters/dns-parameters.xhtml)
- [DNS message format](https://en.wikipedia.org/wiki/Domain_Name_System#DNS_message_format)
- [Implement DNS in a weekend](https://implement-dns.wizardzines.com)