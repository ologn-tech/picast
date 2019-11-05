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
import re
import socket
import threading
from logging import getLogger
from time import sleep
from typing import Dict, List, Optional, Tuple

from picast.discovery import ServiceDiscovery
from picast.settings import Settings
from picast.video import RasberryPiVideo


class RTSPTransport:

    def __init__(self, host, port):
        self.buffer = None
        self._max_attempt = 1000
        self.open_connection(host, port)

    def open_connection(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        for _ in range(self._max_attempt):
            try:
                sock.connect((host, port))
            except Exception:
                sleep(0.5)
            else:
                break
        sock.settimeout(1)
        self.sock = sock

    def close(self):
        self.sock.close()

    def read(self, size) -> bytes:
        if self.buffer:
            if len(self.buffer) > size:
                res = self.buffer[:size]
                self.buffer = self.buffer[size:]
            else:
                res = self.buffer
                self.buffer = None
                if len(res) < size:
                    res += self.sock.recv(size - len(res))
        else:
            res = self.sock.recv(size)
        return res

    def readline(self) -> bytes:
        if self.buffer is None:
            self.buffer = self.sock.recv(1024)
        while True:
            if b'\r\n' in self.buffer:
                (line, self.buffer) = self.buffer.split(b'\r\n', 1)
                return line
            else:
                try:
                    more = self.sock.recv(1024)
                except BlockingIOError:
                    break
                if not more:
                    break
                else:
                    self.buffer += more
        if self.buffer is not None:
            res = self.buffer
            self.buffer = None
            return res
        else:
            return b''

    def write(self, b: bytes):
        return self.sock.sendall(b)


class RtspSink(threading.Thread):

    def __init__(self,  player, logger='picast'):
        super(RtspSink, self).__init__(name='rtsp-server-0', daemon=True)
        self.config = Settings()
        self.logger = getLogger(logger)
        self.player = player
        self.watchdog = 0
        self.csnum = 0
        self.daemon = True
        self.video = RasberryPiVideo()
        self.wfd_parameters = self.config.get_wfd_parameters()
        self.wfd_video_formats = self.video.get_wfd_video_formats()

    def get_rtsp_headers(self) -> Dict[str, Optional[str]]:
        headers = self.read_headers()
        results = {}
        firstline = headers[0]
        regex = re.compile(r"RTSP/1.0 ([0-9]+) (\w+([ ]\w)*)")
        if firstline.startswith('RTSP/1.0'):
            m = regex.match(firstline)
            if m:
                status, reason = m.group(1, 2)
                cmd = None
                url = None
                resp = "{} {}".format(status, reason)  # type: Optional[str]
            else:
                raise ValueError
        else:
            cmd, url, version = firstline.split(' ')
            if version != 'RTSP/1.0':
                raise ValueError
            resp = None
        results['cmd'] = cmd
        results['url'] = url
        results['resp'] = resp
        for h in headers[1:]:
            pos = h.find(':')
            if not pos:
                break
            key = h[:pos]
            val = h[pos + 2:]
            results[key] = val
        return results

    def read_headers(self) -> List[str]:
        headers = []

        line = self.sock.readline()
        while not line:
            line = self.sock.readline()

        while line:
            headers.append(line.decode('UTF-8'))
            line = self.sock.readline()
        self.logger.debug("<< {}".format(headers))
        return headers

    def read_body(self, headers) -> bytes:
        length = headers.get('Content-Length', None)
        if length is None:
            return b''
        length = int(length)
        return self.sock.read(length)

    @staticmethod
    def _rtsp_response_header(cmd: Optional[str] = None, url: Optional[str] = None, res: Optional[str] = None,
                              seq: Optional[str] = None, others: Optional[List[Tuple[str, str]]] = None) -> str:
        if cmd is not None:
            msg = "{0:s} {1:s} RTSP/1.0".format(cmd, url)
        else:
            msg = "RTSP/1.0"
        if res is not None:
            msg += ' {0}\r\nCSeq: {1}\r\n'.format(res, seq)
        else:
            msg += '\r\nCSeq: {}\r\n'.format(seq)
        if others is not None:
            for k, v in others:
                msg += '{}: {}\r\n'.format(k, v)
        msg += '\r\n'
        return msg

    @staticmethod
    def _parse_transport_header(data: str) -> Tuple[bool, str, str]:
        """ Parse Transport header value such as "Transport: RTP/AVP/UDP;unicast;client_port=1028;server_port=5000"
        """
        udp = True
        client_port = '0'
        server_port = '0'
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

    def rtsp_m1(self) -> bool:
        headers = self.get_rtsp_headers()
        if headers['cmd'] != 'OPTIONS':
            return False
        s_data = self._rtsp_response_header(seq=headers['CSeq'], res="200 OK",
                                            others=[("Public", "org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER")])
        self.logger.debug("<-{}".format(s_data))
        self.sock.write(s_data.encode('ASCII'))
        return True

    def rtsp_m2(self) -> bool:
        self.csnum = 100
        s_data = self._rtsp_response_header(seq=str(self.csnum), cmd="OPTIONS",
                                            url="*", others=[('Require', 'org.wfa.wfd1.0')])
        self.logger.debug("<-{}".format(s_data))
        self.sock.write(s_data.encode('ASCII'))
        sleep(0.1)
        headers = self.get_rtsp_headers()
        if headers['CSeq'] != '100' or headers['resp'] != "200 OK":
            return False
        return True

    def rtsp_m3(self) -> bool:
        headers = self.get_rtsp_headers()
        if headers['cmd'] != 'GET_PARAMETER' or headers['url'] != 'rtsp://localhost/wfd1.0':
            return False
        body = self.read_body(headers)
        msg = ''
        for req in body.decode('UTF-8').split('\r\n'):
            if req == '':
                continue
            elif req == 'wfd_client_rtp_ports':
                msg += "wfd_client_rtp_ports: RTP/AVP/UDP;unicast {} 0 mode=play\r\n".format(self.config.rtp_port)
            elif req == 'wfd_video_formats':
                msg += 'wfd_video_formats: {}\r\n'.format(self.wfd_video_formats)
            elif req in self.wfd_parameters:
                msg += '{}: {}\r\n'.format(req, self.wfd_parameters[req])
            else:
                msg += '{}: none\r\n'.format(req)

        m3resp = self._rtsp_response_header(seq=headers['CSeq'], res="200 OK",
                                            others=[('Content-Type', 'text/parameters'),
                                                    ('Content-Length', str(len(msg)))
                                                    ])
        m3resp += msg
        self.logger.debug("<-{}".format(m3resp))
        self.sock.write(m3resp.encode('ASCII'))
        return True

    def rtsp_m4(self) -> bool:
        headers = self.get_rtsp_headers()
        if headers['cmd'] != "SET_PARAMETER" or headers['url'] != "rtsp://localhost/wfd1.0":
            return False
        self.read_body(headers)
        # FIXME: parse body here to retrieve video mode and set actual mode.
        s_data = self._rtsp_response_header(res="200 OK", seq=headers['CSeq'])
        self.logger.debug("<-{}".format(s_data))
        self.sock.write(s_data.encode('ASCII'))
        return True

    def rtsp_m5(self) -> bool:
        headers = self.get_rtsp_headers()
        self.read_body(headers)
        if headers['cmd'] != 'SET_PARAMETER':
            self.logger.debug("M5: got other than SET_PARAMETER request.")
            s_data = self._rtsp_response_header(res="400 Bad Requests", seq=headers['CSeq'])
            self.logger.debug("<-{}".format(s_data))
            self.sock.write(s_data.encode('ASCII'))
            return False
        # FIXME: analyze body to have  'wfd_trigger_method: SETUP'
        s_data = self._rtsp_response_header(res="200 OK", seq=headers['CSeq'])
        self.logger.debug("<-{}".format(s_data))
        self.sock.write(s_data.encode('ASCII'))
        return True

    def rtsp_m6(self) -> Tuple[Optional[str], Optional[str]]:
        self.csnum += 1
        sessionid = None
        server_port = None
        m6req = self._rtsp_response_header(cmd="SETUP",
                                           url="rtsp://{0:s}/wfd1.0/streamid=0".format(self.config.peeraddress),
                                           seq=str(self.csnum),
                                           others=[
                                               ('Transport',
                                                'RTP/AVP/UDP;unicast;client_port={0:d}'.format(self.config.rtp_port))
                                           ])
        self.logger.debug("<-{}".format(m6req))
        self.sock.write(m6req.encode('ASCII'))

        headers = self.get_rtsp_headers()
        if headers['CSeq'] is not None and headers['CSeq'] != str(self.csnum):
            raise ValueError('Unmatch sequence number: {}'.format(headers['CSeq']))
        if 'Transport' in headers:
            assert headers['Transport'] is not None
            udp, client_port, server_port = self._parse_transport_header(headers['Transport'])
            self.logger.debug("server port {}".format(server_port))
        if 'Session' in headers:
            assert headers['Session'] is not None
            sessionid = headers['Session'].split(';')[0]
        return sessionid, server_port

    def rtsp_m7(self, sessionid: str) -> bool:
        self.csnum += 1
        m7req = self._rtsp_response_header(cmd='PLAY',
                                           url='rtsp://{0:s}/wfd1.0/streamid=0'.format(self.config.peeraddress),
                                           seq=str(self.csnum),
                                           others=[('Session', sessionid)])
        self.logger.debug("<-{}".format(m7req))
        self.sock.write(m7req.encode('ASCII'))
        headers = self.get_rtsp_headers()
        if headers['resp'] != "200 OK" or headers['CSeq'] != str(self.csnum):
            return False
        return True

    def negotiate(self) -> bool:
        self.logger.debug("---- Start negotiation ----")
        while True:
            if not self.rtsp_m1():
                break
            if not self.rtsp_m2():
                break
            if not self.rtsp_m3():
                break
            if not self.rtsp_m4():
                break
            if not self.rtsp_m5():
                break
            sessionid, server_port = self.rtsp_m6()
            if sessionid is None:
                break
            if not self.rtsp_m7(sessionid):
                break
            self.logger.info("---- Negotiation successful ----")
            return True
        self.logger.info("---- Negotiation failed ----")
        return False

    def rtspsrv(self, idrsock) -> None:
        self.teardown = False
        while True:
            try:
                headers = self.get_rtsp_headers()
            except socket.error as e:
                self.handle_recv_err(e, idrsock)
            else:
                self.watchdog = 0
                if headers['cmd'] == "GET_PARAMETER" and headers['url'] == "rtsp://localhost/wfd1.0":
                    self.read_body(headers)
                    resp_msg = self._rtsp_response_header(seq=headers['CSeq'], res="200 OK")
                    self.sock.write(resp_msg)
                elif headers['cmd'] == "SET_PARAMETER":
                    body = self.read_body(headers)
                    lines = body.decode('UTF-8').splitlines()
                    if 'wfd_trigger_method: TEARDOWN' in lines:
                        resp_msg = self._rtsp_response_header(seq=headers['CSeq'], res="200 OK")
                        self.sock.write(resp_msg)

                        self.logger.debug("Got TEARDOWN request.")
                        m5_msg = self._rtsp_response_header(seq=str(self.csnum), cmd="TEARDOWN",
                                                            url="rtsp://localhost/wfd1.0")
                        self.sock.write(m5_msg)
                        self.teardown = True
                        self.player.stop()
                elif self.teardown and headers['cmd'] is None and headers['resp'] == "200 OK":
                    break
                else:
                    continue

    def handle_recv_err(self, e, idrsock) -> None:
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
                idrreq = self._rtsp_response_header(seq=str(self.csnum),
                                                    cmd="SET_PARAMETER", url="rtsp://localhost/wfd1.0",
                                                    others=[('Content-Length', str(len(msg))),
                                                            ('Content-Type', 'text/parameters')
                                                            ])
                idrreq += msg
                self.logger.debug("idreq: {}".format(idrreq))
                self.sock.write(idrreq.encode('ASCII'))
        else:
            self.logger.debug("Exit becuase of socket error.")

    def run(self):
        self.logger.info("Register mDNS/SD entry.")
        sd = ServiceDiscovery()
        sd.register()
        self.sock = RTSPTransport(self.config.peeraddress, self.config.rtsp_port)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as idrsock:
            idrsock_address = ('127.0.0.1', 0)
            idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            idrsock.bind(idrsock_address)
            if self.negotiate():
                self.player.start()
                self.rtspsrv(idrsock)
