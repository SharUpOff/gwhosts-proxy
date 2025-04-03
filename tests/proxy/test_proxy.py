import pytest
from gwhosts.proxy import DNSProxy
from gwhosts.dns import QName
from gwhosts.network import UDPSocket
from logging import getLogger
from pytest_mock import MockerFixture
from typing import List


_logger = getLogger("pytest")


@pytest.fixture()
def proxy() -> DNSProxy:
    return DNSProxy(
        hostnames={QName((b"example", b"com"))},
        logger=_logger,
    )


@pytest.mark.parametrize("listdir", ([], ["0"], ["0", "1"], ["0", "1", "2"], ["0", "1", "2", "3"]))
def test_open_files_count(mocker: MockerFixture, proxy: DNSProxy, listdir: List[str]) -> None:
    mock_os_listdir = mocker.patch("os.listdir", return_value=listdir)

    assert proxy._open_files_count == len(listdir)
    mock_os_listdir.assert_called_once_with("/proc/self/fd")


def test_active_pool(proxy: DNSProxy) -> None:
    pass


def test_get_socket(proxy: DNSProxy) -> None:
    free_pool_socket = UDPSocket()
    proxy._free_pool = [free_pool_socket]

    assert proxy._get_socket() is free_pool_socket
    assert len(proxy._free_pool) == 0
    assert proxy._get_socket() is not free_pool_socket


@pytest.mark.parametrize(
    ("hostname", "exists"),
    (
        (QName((b"something", b"example", b"com")), True),
        (QName((b"example", b"com")), True),
        (QName((b"something", b"com")), False),
        (QName((b"com",)), False),
    ),
)
def test_hostname_exists(proxy: DNSProxy, hostname: QName, exists: bool) -> None:
    assert proxy._hostname_exists(hostname) is exists
