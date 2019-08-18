#!/usr/bin/env python3

"""
This software is a pycast, a simple wireless display receiver for Raspberry Pi

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
import subprocess
import sys
import tempfile
from time import sleep

from logging import getLogger, StreamHandler, DEBUG


class Settings:
    player_select = 1
    # 1: vlc
    # 2: Raspberry-Pi
    sound_output_select = 0
    # 0: HDMI sound output
    # 1: 3.5mm audio jack output
    # 2: alsa
    device_name = 'pycast'
    wifi_p2p_group_name = 'persistent'
    pin = '12345678'
    timeout = 300
    myaddress = '192.168.173.1'
    leaseaddress = '192.168.173.80'
    netmask = '255.255.255.0'


class PyCastException(Exception):
    pass


class ProcessManager(object):
    # this class is Borg/Singleton
    _shared_state = {}

    def __new__(cls, *p, **k):
        self = object.__new__(cls)
        self.__dict__ = cls._shared_state
        return self

    def __init__(self):
        self.player = None
        self.dhcpd = None
        self.logger = getLogger("PyCast")

    def start_udhcpd(self, interface):
        fd, self.conf_path = tempfile.mkstemp(suffix='.conf')
        conf = "start  {}\nend {}\ninterface {}\noption subnet {}\noption lease {}\n".format(
            Settings.leaseaddress, Settings.leaseaddress, interface, Settings.netmask, Settings.timeout)
        self.logger.debug(conf)
        with open(self.conf_path, 'w') as c:
            c.write(conf)
        self.dhcpd = subprocess.Popen(["sudo", "udhcpd", self.conf_path])

    def launch_player(self):
        command_list = None
        if Settings.player_select == 1:
            command_list = ['vlc', '--fullscreen', 'rtp://0.0.0.0:1028/wfd1.0/streamid=0']
        elif Settings.player_select == 2:
            command_list = ['omxplayer', 'rtp://0.0.0.0:1028', '-n', '-1', '--live']
        self.logger.debug("Launch player {}".format(command_list[0]))
        self.player = subprocess.Popen(command_list)

    def kill(self):
        if self.player is not None:
            self.player.terminate()
            self.player = None

    def terminate(self):
        if self.player is not None:
            self.player.terminate()
            self.player = None
        if self.dhcpd is not None:
            self.dhcpd.terminate()
            os.unlink(self.conf_path)
            self.dhcpd = None


class WpaCli:
    """
    Wraps the wpa_cli command line interface.
    """

    def __init__(self):
        self.logger = getLogger("PyCast")
        pass

    def cmd(self, arg):
        command_str = "sudo wpa_cli"
        command_list = command_str.split(" ") + arg.split(" ")
        p = subprocess.Popen(command_list, stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        return stdout.decode('UTF-8').splitlines()

    def start_p2p_find(self):
        self.logger.debug("wpa_cli p2p_find type=progressive")
        status = self.cmd("p2p_find type=progressive")
        if 'OK' not in status:
            raise PyCastException("Fail to start p2p find.")

    def stop_p2p_find(self):
        self.logger.debug("wpa_cli p2p_stop_find")
        status = self.cmd("p2p_stop_find")
        if 'OK' not in status:
            raise PyCastException("Fail to stop p2p find.")

    def set_device_name(self, name):
        self.logger.debug("wpa_cli set device_name {}".format(name))
        status = self.cmd("set device_name {}".format(name))
        if 'OK' not in status:
            raise PyCastException("Fail to set device name {}".format(name))

    def set_device_type(self, type):
        self.logger.debug("wpa_cli set device_type {}".format(type))
        status = self.cmd("set device_type {}".format(type))
        if 'OK' not in status:
            raise PyCastException("Fail to set device type {}".format(type))

    def set_p2p_go_ht40(self):
        self.logger.debug("wpa_cli set p2p_go_ht40 1")
        status = self.cmd("set p2p_go_ht40 1")
        if 'OK' not in status:
            raise PyCastException("Fail to set p2p_go_ht40")

    def wfd_subelem_set(self, val):
        self.logger.debug("wpa_cli wfd_subelem_set {}".format(val))
        status = self.cmd("wfd_subelem_set {}".format(val))
        if 'OK' not in status:
            raise PyCastException("Fail to wfd_subelem_set.")

    def p2p_group_add(self, name):
        self.logger.debug("wpa_cli p2p_group_add {}".format(name))
        self.cmd("p2p_group_add {}".format(name))

    def set_wps_pin(self, interface, pin, timeout):
        self.logger.debug("wpa_cli -i {} wps_pin any {} {}".format(interface, pin, timeout))
        status = self.cmd("-i {} wps_pin any {} {}".format(interface, pin, timeout))
        return status

    def get_interfaces(self):
        selected = None
        interfaces = []
        status = self.cmd("interface")
        for ln in status:
            if ln.startswith("Selected interface"):
                selected = re.match(r"Selected interface\s\'(.+)\'$", ln).group(1)
            elif ln.startswith("Available interfaces:"):
                pass
            else:
                interfaces.append(str(ln))
        return selected, interfaces

    def get_p2p_interface(self):
        sel, interfaces = self.get_interfaces()
        for it in interfaces:
            if it.startswith("p2p-wl"):
                return it
        return None

    def check_p2p_interface(self):
        if self.get_p2p_interface() is not None:
            return True
        return False


class PyCast:

    def __init__(self, log=False, loglevel=DEBUG):
        logger = getLogger("PyCast")
        handler = StreamHandler()
        handler.setLevel(DEBUG)
        logger.setLevel(loglevel)
        logger.addHandler(handler)
        logger.propagate = log
        self.logger = logger

    def uibcstart(self, sock, data):
        logger = getLogger("PyCast")
        messagelist = data.splitlines()
        for entry in messagelist:
            if 'wfd_uibc_capability:' in entry:
                entrylist = entry.split(';')
                uibcport = entrylist[-1]
                uibcport = uibcport.split('\r')
                uibcport = uibcport[0]
                uibcport = uibcport.split('=')
                uibcport = uibcport[1]
                logger.info('uibcport: {}'.format(uibcport))

    def wait_connection(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('192.168.173.80', 7236)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connectcounter = 0
        while True:
            try:
                sock.connect(server_address)
            except socket.error as e:
                connectcounter = connectcounter + 1
                if connectcounter > 1024:
                    sock.close()
                    logger = getLogger("PyCast")
                    logger.debug("Exit because of caught maximum connection timeouts(1024 x 180sec ).")
                    return None, None
            else:
                break
        idrsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        idrsock_address = ('127.0.0.1', 0)
        idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        idrsock.bind(idrsock_address)
        addr, idrsockport = idrsock.getsockname()
        self.idrsockport = str(idrsockport)
        return sock, idrsock

    def cast_seq1(self, sock):
        logger = getLogger("PyCast.cseq1")
        data = (sock.recv(1000))
        logger.debug("<-{}".format(data))
        s_data = 'RTSP/1.0 200 OK\r\nCSeq: 1\r\n\Public: org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER\r\n\r\n'
        logger.debug("->{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))

    def cast_seq100(self, sock):
        logger = getLogger("PyCast.cseq100")
        s_data = 'OPTIONS * RTSP/1.0\r\nCSeq: 100\r\nRequire: org.wfa.wfd1.0\r\n\r\n'
        logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))
        data = (sock.recv(1000))
        logger.debug("->{}".format(data))

    def cast_seq2(self, sock):
        logger = getLogger("PyCast.cseq2")
        data = (sock.recv(1000))
        logger.debug("->{}".format(data))
        msg = 'wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\n'
        if Settings.player_select == 2:
            msg = msg + 'wfd_audio_codecs: LPCM 00000002 00\r\n'
        else:
            msg = msg + 'wfd_audio_codecs: AAC 00000001 00\r\n'

        msg = msg + 'wfd_video_formats: 00 00 02 04 0001FFFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n' \
                  + 'wfd_3d_video_formats: none\r\n' \
                  + 'wfd_coupled_sink: none\r\n' \
                  + 'wfd_display_edid: none\r\n' \
                  + 'wfd_connector_type: 05\r\n' \
                  + 'wfd_uibc_capability: none\r\n' \
                  + 'wfd_standby_resume_capability: none\r\n' \
                  + 'wfd_content_protection: none\r\n'

        m3resp = 'RTSP/1.0 200 OK\r\nCSeq: 2\r\n' + 'Content-Type: text/parameters\r\nContent-Length: ' + str(
            len(msg)) + '\r\n\r\n' + msg
        logger.debug("<--------{}".format(m3resp))
        sock.sendall(m3resp.encode("UTF-8"))

    def cast_seq3(self, sock):
        logger = getLogger("PyCast.cseq3")
        data = (sock.recv(1000)).decode("UTF-8")
        logger.debug("->{}".format(data))
        s_data = 'RTSP/1.0 200 OK\r\nCSeq: 3\r\n\r\n'
        logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))
        self.uibcstart(sock, data)

    def cast_seq4(self, sock):
        logger = getLogger("PyCast.cseq4")
        data = (sock.recv(1000))
        logger.debug("->{}".format(data))
        s_data = 'RTSP/1.0 200 OK\r\nCSeq: 4\r\n\r\n'
        logger.debug("<-{}".format(s_data))
        sock.sendall(s_data.encode("UTF-8"))

    def cast_seq5(self, sock):
        logger = getLogger("PyCast.cseq5")
        m6req = 'SETUP rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n' \
                + 'CSeq: 101\r\n' \
                + 'Transport: RTP/AVP/UDP;unicast;client_port=1028\r\n\r\n'
        logger.debug("<-{}".format(m6req))
        sock.sendall(m6req.encode("UTF-8"))
        data = (sock.recv(1000))
        logger.debug("->{}".format(data))
        paralist = data.decode("UTF-8").split(';')
        serverport = [x for x in paralist if 'server_port=' in x]
        logger.debug("server port {}".format(serverport))
        serverport = serverport[-1]
        serverport = serverport[12:17]
        logger.debug("server port {}".format(serverport))
        paralist = data.decode("UTF-8").split()
        position = paralist.index('Session:') + 1
        sessionid = paralist[position]
        return sessionid

    def cast_seq6(self, sock, sessionid):
        logger = getLogger("PyCast.cseq6")
        m7req = 'PLAY rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n' \
                + 'CSeq: 102\r\n' \
                + 'Session: ' + str(sessionid) + '\r\n\r\n'
        logger.debug("<-{}".format(m7req))
        sock.sendall(m7req.encode("UTF-8"))
        data = (sock.recv(1000))
        logger.debug("->{}".format(data))

    def negotiate(self, sock):
        logger = getLogger("PyCast.negotiation")
        self.cast_seq1(sock)
        self.cast_seq100(sock)
        self.cast_seq2(sock)
        self.cast_seq3(sock)
        self.cast_seq4(sock)
        sessionid = self.cast_seq5(sock)
        self.cast_seq6(sock, sessionid)
        logger.debug("---- Negotiation successful ----")

    def start(self, sock, idrsock):
        logger = getLogger("PyCast.control")
        csnum = 102
        watchdog = 0
        while True:
            try:
                data = (sock.recv(1000)).decode("UTF-8")
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    try:
                        (idrsock.recv(1000))
                    except socket.error as e:
                        err = e.args[0]
                        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                            sleep(0.01)
                            watchdog = watchdog + 1
                            if watchdog == 70 / 0.01:
                                self.player_manager.kill()
                                sleep(1)
                                break
                        else:
                            logger.debug("socket error.")
                            return
                    else:
                        csnum = csnum + 1
                        msg = 'wfd-idr-request\r\n'
                        idrreq = 'SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n' \
                                 + 'Content-Length: ' + str(len(msg)) + '\r\n' \
                                 + 'Content-Type: text/parameters\r\n' \
                                 + 'CSeq: ' + str(csnum) + '\r\n\r\n' \
                                 + msg
                        logger.debug("idreq: {}".format(idrreq))
                        sock.sendall(idrreq.encode("UTF-8"))

                else:
                    logger.debug("Exit becuase of socket error.")
                    return
            else:
                logger.debug("data: {}".format(data))
                watchdog = 0
                if len(data) == 0 or 'wfd_trigger_method: TEARDOWN' in data:
                    self.player_manager.kill()
                    sleep(1)
                    break
                elif 'wfd_video_formats' in data:
                    self.player_manager.launch_player()
                messagelist = data.splitlines()
                singlemessagelist = [x for x in messagelist if ('GET_PARAMETER' in x or 'SET_PARAMETER' in x)]
                logger.debug(singlemessagelist)
                for singlemessage in singlemessagelist:
                    entrylist = singlemessage.splitlines()
                    for entry in entrylist:
                        if re.match(r'CSeq:', entry):
                            cseq = entry
                            resp = 'RTSP/1.0 200 OK\r' + cseq + '\r\n\r\n'  # cseq contains \n
                            logger.debug("Response: {}".format(resp))
                            sock.sendall(resp.encode("UTF-8"))
                            break
                self.uibcstart(sock, data)
        idrsock.close()
        sock.close()

    def create_p2p_interface(self):
        wpacli = WpaCli()
        wpacli.start_p2p_find()
        wpacli.set_device_name(Settings.device_name)
        wpacli.set_device_type("7-0050F204-1")
        wpacli.set_p2p_go_ht40()
        wpacli.wfd_subelem_set("0 00060151022a012c")
        wpacli.wfd_subelem_set("1 0006000000000000")
        wpacli.wfd_subelem_set("6 000700000000000000")
        # fixme: detect existent persisntent group and use it
        # perentry="$(wpa_cli list_networks | grep "\[DISABLED\]\[P2P-PERSISTENT\]" | tail -1)"
        # networkid=${perentry%%D*}
        wpacli.p2p_group_add(Settings.wifi_p2p_group_name)

    def set_p2p_interface(self):
        logger = getLogger("PyCast")
        wpacli = WpaCli()
        if wpacli.check_p2p_interface():
            logger.info("Already set a p2p interface.")
            p2p_interface = wpacli.get_p2p_interface()
        else:
            self.create_p2p_interface()
            sleep(3)
            p2p_interface = wpacli.get_p2p_interface()
            if p2p_interface is None:
                raise PyCastException("Can not create P2P Wifi interface.")
            logger.info("Start p2p interface: {}".format(p2p_interface))
            os.system("sudo ifconfig {} {}".format(p2p_interface, Settings.myaddress))
        return p2p_interface

    def run(self):
        logger = getLogger("PyCast")
        self.player_manager = ProcessManager()
        wpacli = WpaCli()
        try:
            wlandev = self.set_p2p_interface()
            self.player_manager.start_udhcpd(wlandev)
            while (True):
                wpacli.set_wps_pin(wlandev, Settings.pin, Settings.timeout)
                sock, idrsock = self.wait_connection()
                if sock is None:
                    continue
                self.negotiate(sock)
                self.player_manager.launch_player()
                fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
                fcntl.fcntl(idrsock, fcntl.F_SETFL, os.O_NONBLOCK)
                self.start(sock, idrsock)
                self.player_manager.terminate()
        except PyCastException as ex:
            if self.player_manager is not None:
                self.player_manager.terminate()
            logger.exception("Got error: {}".format(ex))


if __name__ == '__main__':
    sys.exit(PyCast(log=True, loglevel=DEBUG).run())
