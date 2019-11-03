import asyncio
import socket
import threading

import pytest

from picast.rtspsink import RtspSink
from picast.video import RasberryPiVideo


class MockServer(threading.Thread):

    def __init__(self, port, target="open"):
        super(MockServer, self).__init__()
        self.port = port
        self.target = target
        self.status = True
        self.msg = None

    def run(self):
        self.sock =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('127.0.0.1', self.port))
        self.sock.listen(1)
        conn, remote = self.sock.accept()

        if self.target == "open":
            pass
        elif self.target == "m1":
            m1 = b"OPTIONS * RTSP/1.0\r\nCSeq: 0\r\nRequire: org.wfa.wfd1.0\r\n\r\n"
            conn.sendall(m1)
            m1_resp = conn.recv(1000)
            if m1_resp != b"RTSP/1.0 200 OK\r\nCSeq: 0\r\nPublic: org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER\r\n\r\n":
                self.status = False
                self.msg = "M1 response failure: {}".format(m1_resp)
        elif self.target == "m2":
            m2 = conn.recv(1000)
            if m2 != b"OPTIONS * RTSP/1.0\r\nCSeq: 100\r\nRequire: org.wfa.wfd1.0\r\n\r\n":
                resp_400 = b"RTSP/1.0 400 Bad Request\r\nCSeq: 100\r\n\r\n"
                conn.sendall(resp_400)
                self.status = False
                self.msg = "M2 request failure: {}".format(m2)
            else:
                m2_resp = b"RTSP/1.0 200 OK\r\nCSeq: 100\r\nPublic: org.wfa.wfd1.0, SETUP, TEARDOWN, PLAY, PAUSE, GET_PARAMETER, SET_PARAMETER\r\n\r\n"
                conn.sendall(m2_resp)
        elif self.target == "m3":
            m3_body = "wfd_video_formats\r\nwfd_audio_codecs\r\nwfd_3d_video_formats\r\nwfd_content_protection\r\n" \
                      "wfd_display_edid\r\nwfd_coupled_sink\r\nwfd_client_rtp_ports\r\n"
            m3 = "GET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\nCSeq: 1\r\nContent-Type: text/parameters\r\n" \
                 "Content-Length: {}\r\n\r\n{}".format(len(m3_body), m3_body).encode('ASCII')
            conn.sendall(m3)
            m3_resp = conn.recv(1000).decode('UTF-8')
            if m3_resp != "RTSP/1.0 200 OK\r\nCSeq: 1\r\nContent-Type: text/parameters\r\nContent-Length: 304\r\n\r\n" \
                          "wfd_video_formats: 06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none\r\n" \
                          "wfd_audio_codecs: AAC 00000001 00, LPCM 00000002 00\r\n" \
                          "wfd_3d_video_formats: none\r\n" \
                          "wfd_content_protection: none\r\n" \
                          "wfd_display_edid: none\r\n" \
                          "wfd_coupled_sink: none\r\n" \
                          "wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\n":
                resp_400 = b"RTSP/1.0 400 Bad Request\r\nCSeq: 1\r\n\r\n"
                conn.sendall(resp_400)
                self.status = False
                self.msg = "M3 bad request: {}".format(m3_resp)
        elif self.target == "m4":
                m4 = b"SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\nCSeq: 2\r\nContent-Type: text/parameters\r\nContent-Length: 302\r\n\r\n" \
                     b"wfd_video_formats: 00 00 01 01 00000001 00000000 00000000 00 0000 0000 00 none none\r\nwfd_audio_codecs: LPCM 00000002 00\r\n" \
                     b"wfd_presentation_URL: rtsp://192.168.173.80/wfd1.0/streamid=0 none\r\n" \
                     b"wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\n"
                conn.sendall(m4)
                m4_resp = conn.recv(1000).decode('UTF-8')
                if m4_resp != "RTSP/1.0 200 OK\r\nCSeq: 2\r\n\r\n":
                    self.status = False
                    self.msg = "M4 bad response: {}".format(m4_resp)
        elif self.target == "m5":
            m5 = b"SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n" \
                 b"CSeq: 3\r\nContent-Type: text/paramters\r\nContent-Length: 27\r\n\r\nwfd_trigger_method: SETUP\r\n\r\n"
            conn.sendall(m5)
            m5_resp = conn.recv(1000).decode('UTF-8')
            if m5_resp != "RTSP/1.0 200 OK\r\nCSeq: 3\r\n\r\n":
                self.status = False
                self.msg = "M5 bad response: {}".format(m5_resp)
        elif self.target == "m6":
            m6 = conn.recv(1000)
            if m6 != b"SETUP rtsp://192.168.173.80/wfd1.0/streamid=0 RTSP/1.0\r\nCSeq: 101\r\n" \
                     b"Transport: RTP/AVP/UDP;unicast;client_port=1028\r\n\r\n":
                resp_400 = b"RTSP/1.0 400 Bad Request\r\nCSeq: 101\r\n\r\n"
                conn.sendall(resp_400)
                self.status = False
                self.msg = "M6 request failure: {}".format(m6)
            else:
                m6_resp = b"RTSP/1.0 200 OK\r\nCSeq: 101\r\nSession: 7C9C5678;timeout=30\r\n" \
                          b"Transport: RTP/AVP/UDP;unicast;client_port=1028;server_port=5000\r\n\r\n"
                conn.sendall(m6_resp)
        elif self.target == "m7":
            m7 = conn.recv(1000)
            if m7 != b"PLAY rtsp://192.168.173.80/wfd1.0/streamid=0 RTSP/1.0\r\nCSeq: 102\r\nSession: 7C9C5678\r\n\r\n":
                resp_400 = b"RTSP/1.0 400 Bad Request\r\nCSeq: 102\r\n\r\n"
                conn.sendall(resp_400)
                self.status = False
                self.msg = "M7 request failure: {}".format(m7)
            else:
                m7_resp = b"RTSP/1.0 200 OK\r\nCSeq: 102\r\n\r\n"
                conn.sendall(m7_resp)
        else:
            pass
        conn.close()

    def join(self, *args):
        threading.Thread.join(self, *args)
        return self.status, self.msg


@pytest.mark.asyncio
async def test_open_connection(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port)
    server.start()
    player = None
    rtspserver = RtspSink(player)
    assert await rtspserver.open_connection('127.0.0.1', unused_port)
    server.join()


@pytest.mark.asyncio
async def test_rtsp_m1(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port, target="m1")
    server.start()
    player = None
    rtspserver = RtspSink(player)
    await rtspserver.open_connection('127.0.0.1', unused_port)
    await rtspserver.cast_seq_m1()
    result, msg = server.join()
    if not result:
        pytest.fail(msg)


@pytest.mark.asyncio
async def test_rtsp_m2(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port, target="m2")
    server.start()
    player = None
    rtspserver = RtspSink(player)
    await rtspserver.open_connection('127.0.0.1', unused_port)
    await rtspserver.cast_seq_m2()
    result, msg = server.join()
    if not result:
        pytest.fail(msg)


@pytest.mark.asyncio
async def test_rtsp_m3(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port, target="m3")
    server.start()
    player = None
    rtspserver = RtspSink(player)
    await rtspserver.open_connection('127.0.0.1', unused_port)
    await rtspserver.cast_seq_m3()
    result, msg = server.join()
    if not result:
        pytest.fail(msg)


@pytest.mark.asyncio
async def test_rtsp_m4(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port, target="m4")
    server.start()
    player = None
    rtspserver = RtspSink(player)
    await rtspserver.open_connection('127.0.0.1', unused_port)
    await rtspserver.cast_seq_m4()
    result, msg = server.join()
    if not result:
        pytest.fail(msg)


@pytest.mark.asyncio
async def test_rtsp_m5(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port, target="m5")
    server.start()
    player = None
    rtspserver = RtspSink(player)
    await rtspserver.open_connection('127.0.0.1', unused_port)
    await rtspserver.cast_seq_m5()
    result, msg = server.join()
    if not result:
        pytest.fail(msg)


@pytest.mark.asyncio
async def test_rtsp_m6(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port, target="m6")
    server.start()
    player = None
    rtspserver = RtspSink(player)
    await rtspserver.open_connection('127.0.0.1', unused_port)
    rtspserver.csnum = 100
    await rtspserver.cast_seq_m6()
    result, msg = server.join()
    if not result:
        pytest.fail(msg)


@pytest.mark.asyncio
async def test_rtsp_m7(monkeypatch, unused_port):
    def videomock(self):
        return "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    def nonemock(self, *args):
        return
    monkeypatch.setattr(RasberryPiVideo, "get_wfd_video_formats", videomock)
    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", nonemock)

    server = MockServer(unused_port, target="m7")
    server.start()
    player = None
    rtspserver = RtspSink(player)
    await rtspserver.open_connection('127.0.0.1', unused_port)
    rtspserver.csnum = 101
    sessionid = '7C9C5678'
    await rtspserver.cast_seq_m7(sessionid)
    result, msg = server.join()
    if not result:
        pytest.fail(msg)
