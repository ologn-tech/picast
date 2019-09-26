
import socket
import threading

import pytest

from picast.picast import PiCast


class MockServer(threading.Thread):

    def __init__(self, port):
        super(MockServer, self).__init__()
        self.port = port

    def run(self):
        self.sock =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', self.port))
        self.sock.listen(1)
        conn, remote = self.sock.accept()
        conn.close()


@pytest.mark.unit
def test_connection():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()

    server = MockServer(port)
    server.start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert PiCast._connect(sock, '127.0.0.1', port)
    sock.close()
    server.join()


@pytest.mark.unit
def test_parse_header_200_OK():
    data = "RTSP/1.0 200 OK\r\nCSeq: 1\r\n\r\n"
    headers, body = PiCast._split_header_body(data)
    cmd, url, resp, seq, others = PiCast._rtsp_parse_headers(headers)
    assert cmd is None
    assert url is None
    assert resp == "200 OK"
    assert seq == 1


@pytest.mark.unit
def test_parse_rtsp_parse_header_options():
    data = 'OPTIONS * RTSP/1.0\r\nCSeq: 2\r\n\r\n'
    headers, body = PiCast._split_header_body(data)
    cmd, url, resp, seq, others = PiCast._rtsp_parse_headers(headers)
    assert cmd == 'OPTIONS'
    assert url == '*'
    assert resp is None
    assert seq == 2


@pytest.mark.unit
def test_parse_rtsp_parse_header_setup():
    data = 'SETUP rtsp://192.168.173.80/wfd1.0/streamid=0 RTSP/1.0\r\nCSeq: 3\r\n\r\n'
    headers, body = PiCast._split_header_body(data)
    cmd, url, resp, seq, others = PiCast._rtsp_parse_headers(headers)
    assert cmd == 'SETUP'
    assert url == 'rtsp://192.168.173.80/wfd1.0/streamid=0'
    assert resp is None
    assert seq == 3
