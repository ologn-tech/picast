
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
    assert PiCast.connect(sock, '127.0.0.1', port)
    sock.close()
    server.join()


@pytest.mark.unit
def test_parse_rtsp_header_options():
    header = 'OPTIONS * RTSP/1.0\r\n'
    cmd, url, resp = PiCast.rtsp_parse_command(header)
    assert cmd == 'OPTIONS'
    assert url == '*'
    assert resp is None


@pytest.mark.unit
def test_parse_rtsp_header_response_ok():
    header = 'RTSP/1.0 200 OK\r\n'
    cmd, url, resp = PiCast.rtsp_parse_command(header)
    assert cmd is None
    assert url is None
    assert resp == '200 OK'


@pytest.mark.unit
def test_parse_rtsp_header_setup():
    header = 'SETUP rtsp://192.168.173.80/wfd1.0/streamid=0 RTSP/1.0\r\n'
    cmd, url, resp = PiCast.rtsp_parse_command(header)
    assert cmd == 'SETUP'
    assert url == 'rtsp://192.168.173.80/wfd1.0/streamid=0'
    assert resp is None
