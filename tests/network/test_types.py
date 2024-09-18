from socket import AF_INET, SOCK_DGRAM

from gwhosts.network import (
    UDPSocket,
)


def test_udp_socket() -> None:
    udp_socket = UDPSocket()

    assert udp_socket.type == SOCK_DGRAM
    assert udp_socket.family == AF_INET
