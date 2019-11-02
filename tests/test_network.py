import asyncio
import socket
import threading

import pytest

from picast.rtspsink import RtspSink
from picast.video import RasberryPiVideo


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


@pytest.mark.asyncio
async def test_open_connection(monkeypatch, unused_tcp_port):

    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"

    def nonemock(self, *args):
        return

    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_tcp_port)
    server.start()
    player = None
    rtspserver = RtspSink(player)
    assert await rtspserver.open_connection('127.0.0.1', unused_tcp_port)
    server.join()
