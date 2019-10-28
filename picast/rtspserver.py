#!/usr/bin/env python3

"""
picast - a simple wireless display receiver for Raspberry Pi

    Copyright (C) 2019 Hiroshi Miura
    Copyright (C) 2018 Hsun-Wei Cho

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import errno
import fcntl
import os
import socket
import threading
from logging import getLogger
from time import sleep

from picast.discovery import ServiceDiscovery
from picast.settings import Settings
from picast.video import WfdVideoParameters


class RtspServer(threading.Thread):

    def __init__(self, player, logger='picast'):
        super(RtspServer, self).__init__(name='rtsp-server-0', daemon=True)
        self.config = Settings()
        self.logger = getLogger(logger)
        self.player = player
        self.watchdog = 0
        self.csnum = 0
        self.daemon = True

    @staticmethod
    def _rtsp_parse_headers(headers):
        firstline = headers[0]
        if firstline.startswith('RTSP/1.0'):
            version, status, reason = firstline.split(' ')
            cmd = None
            url = None
            resp = "{} {}".format(status, reason)
        else:
            cmd, url, version = firstline.split(' ')
            if version != 'RTSP/1.0':
                raise ValueError
            resp = None
        seq = 0
        others = {}
        for h in headers[1:]:
            pos = h.find(':')
            key = h[:pos]
            val = h[pos+2:]
            if key == 'CSeq':
                seq = int(val)
            else:
                others[key] = val
        return cmd, url, resp, seq, others

    @staticmethod
    def _rtsp_response_header(cmd=None, url=None, res=None, seq=None, others=None):
        if cmd is not None:
            msg = "{0:s} {1:s} RTSP/1.0".format(cmd, url)
        else:
            msg = "RTSP/1.0"
        if res is not None:
            msg += ' {0:s}\r\nCSeq: {1:d}\r\n'.format(res, seq)
        else:
            msg += '\r\nCSeq: {0:d}\r\n'.format(seq)
        if others is not None:
            for k, v in others:
                msg += '{}: {}\r\n'.format(k, v)
        msg += '\r\n'
        return msg

    @staticmethod
    def _split_header_body(data):
        pos = data.find('\r\n\r\n')
        if pos > 0:
            headers = data[:pos].split('\r\n')
            body = data[pos+4:]
        else:
            raise ValueError
        return headers, body

    @staticmethod
    def _connect(sock: socket, remote: str, port: int) -> bool:
        max_trial = 1200
        for _ in range(max_trial):
            try:
                sock.connect((remote, port))
            except Exception:
                sleep(0.1)
            else:
                return True
        return False

    @staticmethod
    def _parse_transport_header(data):
        """ Parse Transport header value such as "Transport: RTP/AVP/UDP;unicast;client_port=1028;server_port=5000"
        """
        udp = True
        client_port = 0
        server_port = 0
        paramlist = data.split(';')
        for p in paramlist:
            if p.startswith('RTP'):
                rtp, avp, prot = p.split('/')
                if prot == 'UDP':
                    udp = True
                elif prot == 'TCP':
                    udp = False
                else:
                    raise ValueError
            elif p.startswith('unicast'):
                pass
            elif p.startswith('client_port'):
                _, client_port = p.split('=')
            elif p.startswith('server_port'):
                _, server_port = p.split('=')
            else:
                continue
        return udp, client_port, server_port

    def cast_seq_m1(self, sock):
        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if cmd != 'OPTIONS':
            return False
        s_data = self._rtsp_response_header(seq=seq, res="200 OK", others=[("Public", "org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER")])
        self.logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))
        return True

    def cast_seq_m2(self, sock):
        self.csnum = 100
        s_data = self._rtsp_response_header(seq=self.csnum, cmd="OPTIONS", url="*", others=[('Require', 'org.wfa.wfd1.0')])
        self.logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))
        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if seq != 100 or resp  != "200 OK":
            return False
        return True

    def cast_seq_m3(self, sock):
        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if cmd != 'GET_PARAMETER' or url != 'rtsp://localhost/wfd1.0':
            return False
        # audio_codec: LPCM:0x01, AAC:0x02, AC3:0x04
        # audio_sampling_frequency: 44.1khz:1, 48khz:2
        # LPCM: 44.1kHz, 16b; 48 kHZ,16b
        # AAC: 48 kHz, 16b, 2 channels; 48kHz,16b, 4 channels, 48 kHz,16b,6 channels
        # AAC 00000001 00  : 2 ch AAC 48kHz
        msg = 'wfd_audio_codecs: AAC 00000001 00, LPCM 00000002 00\r\n'
        msg += "wfd_client_rtp_ports: RTP/AVP/UDP;unicast {} 0 mode=play\r\n".format(self.config.rtp_port)
        msg += 'wfd_video_formats: {}'.format(WfdVideoParameters().get_video_parameter())
        msg += 'wfd_3d_video_formats: none\r\n'
        msg += 'wfd_coupled_sink: none\r\n'
        msg += 'wfd_display_edid: none\r\n'
        msg += 'wfd_connector_type: 05\r\n'
        msg += 'wfd_uibc_capability: none\r\n'
        msg += 'wfd_standby_resume_capability: none\r\n'
        msg += 'wfd_content_protection: none\r\n'
        m3resp = self._rtsp_response_header(seq=seq, res="200 OK",
                                           others=[('Content-Type', 'text/parameters'),
                                                   ('Content-Length', len(msg))
                                                   ])
        m3resp += msg
        self.logger.debug("<-{}".format(m3resp))
        sock.sendall(m3resp.encode("UTF-8"))
        return True

    def cast_seq_m4(self, sock):
        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if cmd != "SET_PARAMETER" or url != "rtsp://localhost/wfd1.0":
            return False
        # FIXME: parse request body
        s_data = self._rtsp_response_header(res="200 OK", seq=seq)
        self.logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))
        return True

    def cast_seq_m5(self, sock):
        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if cmd != 'SET_PARAMETER':
            self.logger.debug("M5: got other than SET_PARAMETER request.")
            return False
        s_data = self._rtsp_response_header(res="200 OK", seq=seq)
        self.logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))
        return True

    def cast_seq_m6(self, sock):
        self.csnum += 1
        m6req = self._rtsp_response_header(cmd="SETUP",
                                          url="rtsp://{0:s}/wfd1.0/streamid=0".format(self.config.peeraddress),
                                          seq=self.csnum,
                                          others=[
                                              ('Transport',
                                               'RTP/AVP/UDP;unicast;client_port={0:d}'.format(self.config.rtp_port))
                                          ])
        self.logger.debug("<-{}".format(m6req))
        sock.sendall(m6req.encode("UTF-8"))

        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if seq != self.csnum:
            return False
        if 'Transport' in others:
            udp, client_port, server_port = self._parse_transport_header(others['Transport'])
            self.logger.debug("server port {}".format(server_port))
        if 'Session' in others:
            sessionid = others['Session'].split(';')[0]
        return sessionid, server_port

    def cast_seq_m7(self, sock, sessionid):
        self.csnum += 1
        m7req = self._rtsp_response_header(cmd='PLAY',
                                          url='rtsp://{0:s}/wfd1.0/streamid=0'.format(self.config.peeraddress),
                                          seq=self.csnum,
                                          others=[('Session', sessionid)])
        self.logger.debug("<-{}".format(m7req))
        sock.sendall(m7req.encode("UTF-8"))

        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if resp != "200 OK" or seq != self.csnum:
            return False
        return True

    def negotiate(self, conn) -> bool:
        self.logger.debug("---- Start negotiation ----")
        if self.cast_seq_m1(conn) and self.cast_seq_m2(conn) and self.cast_seq_m3(conn) and \
           self.cast_seq_m4(conn) and self.cast_seq_m5(conn):
            sessionid, server_port = self.cast_seq_m6(conn)
            self.cast_seq_m7(conn, sessionid)
            self.logger.info("---- Negotiation successful ----")
            return True
        else:
            self.logger.info("---- Negotiation failed ----")
            return False

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sd = ServiceDiscovery()
            self.logger.info("Register mDNS/SD entry.")
            sd.register()
            self.logger.info("Start connecting...")
            # FIXME: wait for dhcpd leased an address to new client here then initiating to connect
            if self._connect(sock, self.config.peeraddress, self.config.rtsp_port):
                self.logger.info("Connected to Wfd-source in {}.".format(self.config.peeraddress))
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as idrsock:
                    idrsock_address = ('127.0.0.1', 0)
                    idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    idrsock.bind(idrsock_address)
                    addr, idrsockport = idrsock.getsockname()
                    self.idrsockport = str(idrsockport)
                    if self.negotiate(sock):
                        self.player.start()
                        fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
                        fcntl.fcntl(idrsock, fcntl.F_SETFL, os.O_NONBLOCK)
                        self.rtspsrv(sock, idrsock)
            else:
                self.logger.debug("Fails to connect. Wait for peer...")
                sleep(30)

    def rtspsrv(self, conn, idrsock):
        self.teardown = False
        while True:
            try:
                data = conn.recv(1000).decode("UTF-8")
            except socket.error as e:
                self.handle_recv_err(e, conn, idrsock)
            else:
                self.watchdog = 0
                self.logger.debug("->{}".format(data))
                headers, body = self._split_header_body(data)
                cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
                if cmd == "GET_PARAMETER" and url == "rtsp://localhost/wfd1.0":
                    resp_msg = self._rtsp_response_header(seq=seq, res="200 OK")
                    conn.sendall(resp_msg.encode("UTF-8"))
                elif cmd == "SET_PARAMETER" and 'wfd_trigger_method: TEARDOWN' in body:
                    resp_msg = self._rtsp_response_header(seq=seq, res="200 OK")
                    conn.sendall(resp_msg.encode("UTF-8"))
                    self.logger.debug("Got TEARDOWN request.")
                    m5_msg = self._rtsp_response_header(seq=self.csnum, cmd="TEARDOWN",
                                                        url="rtsp://localhost/wfd1.0")
                    conn.sendall(m5_msg.encode("UTF-8"))
                    self.teardown = True
                    self.player.stop()
                elif self.teardown and cmd is None and resp == "200 OK":
                    break
                else:
                    continue

    def handle_recv_err(self, e, sock, idrsock) -> int:
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            try:
                (idrsock.recv(1000))
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    sleep(0.01)
                    self.watchdog += 1
                    if self.watchdog >= 70 / 0.01:
                        self.player.stop()
                        sleep(1)
                else:
                    self.logger.debug("socket error.")
            else:
                self.csnum += 1
                msg = 'wfd-idr-request\r\n'
                idrreq = self._rtsp_response_header(seq=self.csnum,
                                                   cmd="SET_PARAMETER", url="rtsp://localhost/wfd1.0",
                                                   others=[
                                                       ('Content-Length', len(msg)),
                                                       ('Content-Type', 'text/parameters')
                                                   ])
                idrreq += msg
                self.logger.debug("idreq: {}".format(idrreq))
                sock.sendall(idrreq.encode("UTF-8"))
        else:
            self.logger.debug("Exit becuase of socket error.")
