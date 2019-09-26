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
import re
import socket
import threading
from logging import getLogger
from time import sleep

from picast.discovery import ServiceDiscovery
from picast.settings import Settings
from picast.video import WfdVideoParameters


class PiCastException(Exception):
    pass


class PiCast(threading.Thread):

    def __init__(self, player, logger='picast'):
        super(PiCast, self).__init__(name='picast-rtsp-0', daemon=True)
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
        s_data = self._rtsp_response_header(seq=seq, res="200 OK", others=[("Public", "org.wfs.wfd1.0, SET_PARAMETER, GET_PARAMETER")])
        self.logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))
        return True

    def cast_seq_m2(self, sock):
        s_data = self._rtsp_response_header(seq=100, cmd="OPTIONS", url="*", others=[('Require', 'org.wfs.wfd1.0')])
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
        msg = "wfd_client_rtp_ports: RTP/AVP/UDP;unicast {} 0 mode=play\r\n".format(self.config.rtp_port)\
              + WfdVideoParameters().get_video_parameter()
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
        m6req = self._rtsp_response_header(cmd="SETUP",
                                          url="rtsp://{0:s}/wfd1.0/streamid=0".format(self.config.peeraddress),
                                          seq=101,
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
        if 'Transport' in others:
            udp, client_port, server_port = self._parse_transport_header(others['Transport'])
            self.logger.debug("server port {}".format(server_port))
        if 'Session' in others:
            sessionid = others['Session'].split(';')[0]
        return sessionid, server_port

    def cast_seq_m7(self, sock, sessionid):
        m7req = self._rtsp_response_header(cmd='PLAY',
                                          url='rtsp://{0:s}/wfd1.0/streamid=0'.format(self.config.peeraddress),
                                          seq=102,
                                          others=[('Session', sessionid)])
        self.logger.debug("<-{}".format(m7req))
        sock.sendall(m7req.encode("UTF-8"))

        data = sock.recv(1000).decode("UTF-8")
        self.logger.debug("->{}".format(data))
        headers, body = self._split_header_body(data)
        cmd, url, resp, seq, others = self._rtsp_parse_headers(headers)
        if resp != "200 OK" or seq != 102:
            return False
        return True


    def handle_recv_err(self, e, sock, idrsock, csnum) -> int:
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
                csnum = csnum + 1
                msg = 'wfd-idr-request\r\n'
                idrreq = self._rtsp_response_header(seq=csnum,
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
        return csnum

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

    def rtspsrv(self, conn, idrsock):
        fcntl.fcntl(conn, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(idrsock, fcntl.F_SETFL, os.O_NONBLOCK)
        csnum = 102
        while True:
            try:
                data = (conn.recv(1000)).decode("UTF-8")
            except socket.error as e:
                watchdog, csnum = self.handle_recv_err(e, conn, idrsock, csnum)
            else:
                self.logger.debug("->{}".format(data))
                self.watchdog = 0
                if len(data) == 0 or 'wfd_trigger_method: TEARDOWN' in data:
                    self.player.stop()
                    sleep(1)
                    break
                elif 'wfd_video_formats' in data:
                    self.logger.info('start player')
                    self.player.start()
                messagelist = data.splitlines()
                singlemessagelist = [x for x in messagelist if ('GET_PARAMETER' in x or 'SET_PARAMETER' in x)]
                self.logger.debug(singlemessagelist)
                for singlemessage in singlemessagelist:
                    entrylist = singlemessage.splitlines()
                    for entry in entrylist:
                        if re.match(r'CSeq:', entry):
                            cseq = entry.rstrip()
                            resp = self._rtsp_response_header(seq=cseq, res="200 OK")
                            self.logger.debug("<-{}".format(resp))
                            conn.sendall(resp.encode("UTF-8"))
                            continue

    @staticmethod
    def connect(sock: socket, remote: str, port: int) -> bool:
        max_trial = 1200
        for _ in range(max_trial):
            try:
                sock.connect((remote, port))
            except Exception:
                sleep(0.1)
            else:
                return True
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
            if self.connect(sock, self.config.peeraddress, self.config.rtsp_port):
                self.logger.info("Connected to Wfd-source in {}.".format(self.config.peeraddress))
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as idrsock:
                    idrsock_address = ('127.0.0.1', 0)
                    idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    idrsock.bind(idrsock_address)
                    addr, idrsockport = idrsock.getsockname()
                    self.idrsockport = str(idrsockport)
                    if self.negotiate(sock):
                        self.rtspsrv(sock, idrsock)
            else:
                self.logger.debug("Fails to connect. Wait for peer...")
                sleep(30)
