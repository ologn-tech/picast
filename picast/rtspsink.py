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

import asyncio
import errno
import re
import socket
from logging import getLogger
from time import sleep
from typing import List

from picast.discovery import ServiceDiscovery
from picast.settings import Settings
from picast.video import RasberryPiVideo


class RtspSink:

    def __init__(self,  player, logger='picast'):
        self.config = Settings()
        self.logger = getLogger(logger)
        self.player = player
        self.watchdog = 0
        self.csnum = 0
        self.daemon = True
        self.video = RasberryPiVideo()
        self.wfd_parameters = self.config.get_wfd_parameters()
        self.wfd_video_formats = self.video.get_wfd_video_formats()
        self._attempt = 0
        self._max_attempt = 1000
        self._reader = None
        self._writer = None

    async def get_rtsp_headers(self):
        headers = await self.read_headers()
        results = {}
        firstline = headers[0]
        regex = re.compile(r"RTSP/1.0 ([0-9]+) (\w+([ ]\w)*)")
        if firstline.startswith('RTSP/1.0'):
            m = regex.match(firstline)
            if m:
                status, reason = m.group(1, 2)
                cmd = None
                url = None
                resp = "{} {}".format(status, reason)
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
            key = h[:pos]
            val = h[pos + 2:]
            results[key] = val
        return results

    async def read_headers(self) -> List[str]:
        inputs = await self._reader.readline()
        line = inputs.decode('UTF-8')
        headers = []
        while line != '\r\n':
            headers.append(line.rsplit('\r\n')[0])
            inputs = await self._reader.readline()
            line = inputs.decode('UTF-8')
        self.logger.debug("<< {}".format(headers))
        print(headers)
        return headers

    async def read_body(self, headers) -> bytes:
        length = headers.get('Content-Length', None)
        if length is None:
            return b''
        return await self._reader.read(int(length))

    @staticmethod
    def _rtsp_response_header(cmd=None, url=None, res=None, seq=None, others=None):
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

    async def cast_seq_m1(self):
        headers = await self.get_rtsp_headers()
        if headers['cmd'] != 'OPTIONS':
            return False
        s_data = self._rtsp_response_header(seq=headers['CSeq'], res="200 OK",
                                            others=[("Public", "org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER")])
        self.logger.debug("<-{}".format(s_data))
        self._writer.write(s_data.encode('ASCII'))
        await self._writer.drain()

        return True

    async def cast_seq_m2(self):
        self.csnum = 100
        s_data = self._rtsp_response_header(seq=self.csnum, cmd="OPTIONS",
                                            url="*", others=[('Require', 'org.wfa.wfd1.0')])
        self.logger.debug("<-{}".format(s_data))
        self._writer.write(s_data.encode('ASCII'))
        await self._writer.drain()

        headers = await self.get_rtsp_headers()
        if headers['CSeq'] != '100' or headers['resp'] != "200 OK":
            return False
        return True

    async def cast_seq_m3(self):
        headers = await self.get_rtsp_headers()
        if headers['cmd'] != 'GET_PARAMETER' or headers['url'] != 'rtsp://localhost/wfd1.0':
            return False
        body = await self.read_body(headers)
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
                                                    ('Content-Length', len(msg))
                                                    ])
        self.logger.debug("<-{}".format(m3resp))
        self._writer.write(m3resp.encode('ASCII'))
        self._writer.write(msg.encode('ASCII'))
        await self._writer.drain()
        return True

    async def cast_seq_m4(self):
        headers = await self.get_rtsp_headers()
        if headers['cmd'] != "SET_PARAMETER" or headers['url'] != "rtsp://localhost/wfd1.0":
            return False
        await self.read_body(headers)
        # FIXME: parse body here to retrieve video mode and set actual mode.
        s_data = self._rtsp_response_header(res="200 OK", seq=headers['CSeq'])
        self.logger.debug("<-{}".format(s_data))
        self._writer.write(s_data.encode('ASCII'))
        await self._writer.drain()
        return True

    async def cast_seq_m5(self):
        headers = await self.get_rtsp_headers()
        await self.read_body(headers)
        if headers['cmd'] != 'SET_PARAMETER':
            self.logger.debug("M5: got other than SET_PARAMETER request.")
            s_data = self._rtsp_response_header(res="400 Bad Requests", seq=headers['CSeq'])
            self.logger.debug("<-{}".format(s_data))
            self._writer.write(s_data.encode('ASCII'))
            await self._writer.drain()
            return False
        # FIXME: analyze body to have  'wfd_trigger_method: SETUP'
        s_data = self._rtsp_response_header(res="200 OK", seq=headers['CSeq'])
        self.logger.debug("<-{}".format(s_data))
        self._writer.write(s_data.encode('ASCII'))
        await self._writer.drain()
        return True

    async def cast_seq_m6(self):
        self.csnum += 1
        sessionid = None
        server_port = None
        m6req = self._rtsp_response_header(cmd="SETUP",
                                           url="rtsp://{0:s}/wfd1.0/streamid=0".format(self.config.peeraddress),
                                           seq=self.csnum,
                                           others=[
                                               ('Transport',
                                                'RTP/AVP/UDP;unicast;client_port={0:d}'.format(self.config.rtp_port))
                                           ])
        self.logger.debug("<-{}".format(m6req))
        self._writer.write(m6req.encode('ASCII'))
        await self._writer.drain()

        headers = await self.get_rtsp_headers()
        if headers['CSeq'] != self.csnum:
            return False
        if 'Transport' in headers:
            udp, client_port, server_port = self._parse_transport_header(headers['Transport'])
            self.logger.debug("server port {}".format(server_port))
        if 'Session' in headers:
            sessionid = headers['Session'].split(';')[0]
        return sessionid, server_port

    async def cast_seq_m7(self, sessionid):
        self.csnum += 1
        m7req = self._rtsp_response_header(cmd='PLAY',
                                           url='rtsp://{0:s}/wfd1.0/streamid=0'.format(self.config.peeraddress),
                                           seq=self.csnum,
                                           others=[('Session', sessionid)])
        self.logger.debug("<-{}".format(m7req))
        self._writer.write(m7req)
        await self._writer.drain()
        headers = await self.get_rtsp_headers()
        if headers['resp'] != "200 OK" or headers['CSeq'] != self.csnum:
            return False
        return True

    async def negotiate(self) -> bool:
        self.logger.debug("---- Start negotiation ----")
        if await self.cast_seq_m1() and await self.cast_seq_m2() and await self.cast_seq_m3() and \
           await self.cast_seq_m4() and await self.cast_seq_m5():
            sessionid, server_port = await self.cast_seq_m6()
            await self.cast_seq_m7(sessionid)
            self.logger.info("---- Negotiation successful ----")
            return True
        else:
            self.logger.info("---- Negotiation failed ----")
            return False

    async def open_connection(self, host, port):
        while self._max_attempt == 0 or self._attempt < self._max_attempt:
            self._attempt += 1
            await asyncio.sleep(1)
            try:
                self._reader, self._writer = await asyncio.open_connection(host, port)
                return True
            except ConnectionRefusedError:
                pass
        return False

    async def run(self):
        self.logger.info("Register mDNS/SD entry.")
        sd = ServiceDiscovery()
        sd.register()
        self.logger.info("Start connecting...")
        # FIXME: wait for dhcpd leased an address to new client here then initiating to connect
        while True:
            if self.open_connection(self.config.peeraddress, self.config.rtsp_port):
                self.logger.info("Connected to Wfd-source in {}.".format(self.config.peeraddress))
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as idrsock:
                    idrsock_address = ('127.0.0.1', 0)
                    idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    idrsock.bind(idrsock_address)
                    if self.negotiate():
                        self.player.start()
                        await self.rtspsrv(idrsock)
            else:
                pass

    async def rtspsrv(self, idrsock):
        self.teardown = False
        while True:
            self.watchdog = 0
            headers = await self.get_rtsp_headers()
            if headers['cmd'] == "GET_PARAMETER" and headers['url'] == "rtsp://localhost/wfd1.0":
                await self.read_body(headers)
                resp_msg = self._rtsp_response_header(seq=headers['CSeq'], res="200 OK")
                self._writer.write(resp_msg)
                await self._writer.drain()
            elif headers['cmd'] == "SET_PARAMETER":
                body = await self.read_body(headers)
                if 'wfd_trigger_method: TEARDOWN' in body:
                    resp_msg = self._rtsp_response_header(seq=headers['CSeq'], res="200 OK")
                    self._writer.write(resp_msg)
                    await self._writer.drain()

                    self.logger.debug("Got TEARDOWN request.")
                    m5_msg = self._rtsp_response_header(seq=self.csnum, cmd="TEARDOWN",
                                                        url="rtsp://localhost/wfd1.0")
                    self._writer.write(m5_msg)
                    await self._writer.drain()
                    self.teardown = True
                    self.player.stop()
            elif self.teardown and headers['cmd'] is None and headers['resp'] == "200 OK":
                break
            else:
                continue

    async def handle_recv_err(self, e, idrsock):
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
                msg = b'wfd-idr-request\r\n'
                idrreq = self._rtsp_response_header(seq=self.csnum,
                                                    cmd="SET_PARAMETER", url="rtsp://localhost/wfd1.0",
                                                    others=[
                                                        ('Content-Length', len(msg)),
                                                        ('Content-Type', 'text/parameters')
                                                    ])
                self.logger.debug("idreq: {}{}".format(idrreq, msg))
                self._writer.write(idrreq)
                self._writer.write(msg)
                await self._writer.drain()
        else:
            self.logger.debug("Exit becuase of socket error.")
