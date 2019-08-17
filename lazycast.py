#!/usr/bin/env python3

"""
	This software is part of lazycast, a simple wireless display receiver for Raspberry Pi
	Copyright (C) 2018 Hsun-Wei Cho
	Copyright (C) 2019 Hiroshi Miura

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

import psutil
from twisted.internet.selectreactor import SelectReactor
from wpa_supplicant.core import WpaSupplicantDriver

import errno
import fcntl
import logging
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from time import sleep


class Settings:
    player_select = 2
    # 0: non-RPi systems. (using vlc)
    # 1: player1 has lower latency.
    # 2: player2 handles still images and sound better.
    sound_output_select = 0
    # 0: HDMI sound output
    # 1: 3.5mm audio jack output
    # 2: alsa
    disable_1920_1080_60fps = 1
    enable_mouse_keyboard = 1

cur_dir = os.path.dirname(os.path.realpath(__file__))


class WpaLib():

    def __init__(self):
        reactor = SelectReactor()
        threading.Thread(target=reactor.run, kwargs={'installSignalHandlers': 0}).start()
        time.sleep(0.1)  # let reactor start
        driver = WpaSupplicantDriver(reactor)
        self.supplicant = driver.connect()

    def check_p2p(self):
        it = self.get_p2p_interface()
        if it is None:
            return False
        return True

    def get_p2p_interface(self):
        interfaces = self.supplicant.get_interfaces()
        for it in interfaces:
            ifname = it.get_ifname()
            if str(ifname).startswith('p2p-wl'):
                return ifname
        return None


class WpaCli():
    """
    Wraps the wpa_cli command line interface.
    """

    def __init__(self):
        pass

    def cmd(self, arg):
        command_str = "sudo wpa_cli"
        command_list = command_str.split(" ") + arg.split(" ")
        p = subprocess.Popen(command_list, stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        return stdout

    def start_p2p_find(self):
        status = self.cmd("p2p-find type=progressive")
        if status != "OK\n":
            raise Exception("Fail to start p2p find.")

    def stop_p2p_find(self):
        status = self.cmd("p2p-stop-find")
        if status != "OK\n":
            raise Exception("Fail to stop p2p find.")

    def set_device_name(self, name):
        status = self.cmd("set device_name {}".format(name))
        if status != "OK\n":
            raise Exception("Fail to set device name {}".format(name))

    def set_device_type(self, type):
        status = self.cmd("set device_type {}".format(type))
        if status != "OK\n":
            raise Exception("Fail to set device type {}".format(type))

    def set_p2p_go_ht40(self):
        status = self.cmd("set p2p_go_ht40 1")
        if status != "OK\n":
            raise Exception("Fail to set p2p_go_ht40")

    def wfd_subelem_set(self, val):
        status = self.cmd("wfd_subelem_set {}".format(val))
        if status != "OK\n":
            raise Exception("Fail to wfd_subelem_set.")

    def p2p_group_add(self, name):
        status = self.cmd("p2p_group_add {}".format(name))

    def set_wps_pin(self, interface, pin, timeout):
        status = self.cmd("-i {} wps_pin any {} {}".format(interface, pin, timeout))
        return status


class D2():

    def pkill(self, proc_names):
        for proc in psutil.process_iter():
            if proc.name() in proc_names:
                proc.kill()

    def uibcstart(self, sock, data):
        messagelist = data.split('\r\n\r\n')
        for entry in messagelist:
            if 'wfd_uibc_capability:' in entry:
                entrylist = entry.split(';')
                uibcport = entrylist[-1]
                uibcport = uibcport.split('\r')
                uibcport = uibcport[0]
                uibcport = uibcport.split('=')
                uibcport = uibcport[1]
                logging.info('uibcport:' + uibcport + "\n")
                if 'none' not in uibcport and Settings.enable_mouse_keyboard == 1:
                    self.pkill(['control.bin', 'controlhidc.bin'])
                    if ('hidc_cap_list=none' not in entry):
                        pid = subprocess.Popen([os.path.join(cur_dir, 'control', 'controlhidc.bin'), uibcport])
                    elif ('generic_cap_list=none' not in entry):
                        pid = subprocess.Popen([os.path.join(cur_dir, 'control', 'control.bin'), uibcport])

    def start_server(self):
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
                if connectcounter == 20:
                    sock.close()
                    sys.exit(1)
            else:
                break
        idrsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        idrsock_address = ('127.0.0.1', 0)
        idrsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        idrsock.bind(idrsock_address)
        addr, idrsockport = idrsock.getsockname()
        self.idrsockport = str(idrsockport)
        data = (sock.recv(1000))
        return sock, idrsock, data

    def launchplayer(self, player_select):
        self.pkill(['vlc', 'player.bin', 'h264.bin'])
        command_list = None
        if player_select == 1:
            command_list = ['vlc', '--fullscreen', 'rtp://0.0.0.0:1028/wfd1.0/streamid=0']
        elif player_select == 1:
            command_list = [os.path.join(cur_dir, 'player', 'player.bin'), self.idrsockport,
                            str(Settings.sound_output_select)]
        elif player_select == 2:
            command_list = [os.path.join(cur_dir, 'h264', 'h264.bin'), self.idrsockport, str(Settings.sound_output_select)]
        elif player_select == 3:
            command_list = ['omxplayer', 'rtp://0.0.0.0:1028', '-n', '-1', '--live']
        player_pid = subprocess.Popen(command_list)


    def run(self):
        sock, idrsock, data = self.start_server()
        logging.debug( "---M1--->\n" + data)
        s_data = 'RTSP/1.0 200 OK\r\nCSeq: 1\r\n\Public: org.wfa.wfd1.0, SET_PARAMETER, GET_PARAMETER\r\n\r\n'
        logging.debug("<--------\n" + s_data)
        sock.sendall(s_data)
        # M2
        s_data = 'OPTIONS * RTSP/1.0\r\nCSeq: 100\r\nRequire: org.wfa.wfd1.0\r\n\r\n'
        logging.debug("<---M2---\n" + s_data)
        sock.sendall(s_data)
        data = (sock.recv(1000))
        logging.debug("-------->\n" + data)
        # M3
        data = (sock.recv(1000))
        logging.debug("---M3--->\n" + data)
        msg = 'wfd_client_rtp_ports: RTP/AVP/UDP;unicast 1028 0 mode=play\r\n'
        if Settings.player_select == 2:
            msg = msg + 'wfd_audio_codecs: LPCM 00000002 00\r\n'
        else:
            msg = msg + 'wfd_audio_codecs: AAC 00000001 00\r\n'

        if Settings.disable_1920_1080_60fps == 1:
            msg = msg + 'wfd_video_formats: 00 00 02 04 0001FEFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'
        else:
            msg = msg + 'wfd_video_formats: 00 00 02 04 0001FFFF 3FFFFFFF 00000FFF 00 0000 0000 00 none none\r\n'

        msg = msg + 'wfd_3d_video_formats: none\r\n' \
              + 'wfd_coupled_sink: none\r\n' \
              + 'wfd_display_edid: none\r\n' \
              + 'wfd_connector_type: 05\r\n' \
              + 'wfd_uibc_capability: input_category_list=GENERIC, HIDC;generic_cap_list=Keyboard, Mouse;hidc_cap_list=Keyboard/USB, Mouse/USB;port=none\r\n' \
              + 'wfd_standby_resume_capability: none\r\n' \
              + 'wfd_content_protection: none\r\n'

        m3resp = 'RTSP/1.0 200 OK\r\nCSeq: 2\r\n' + 'Content-Type: text/parameters\r\nContent-Length: ' + str(
            len(msg)) + '\r\n\r\n' + msg
        logging.debug("<--------\n" + m3resp)
        sock.sendall(m3resp)

        # M4
        data = (sock.recv(1000))
        logging.debug("---M4--->\n" + data)
        s_data = 'RTSP/1.0 200 OK\r\nCSeq: 3\r\n\r\n'
        logging.debug("<--------\n" + s_data)
        sock.sendall(s_data)

        self.uibcstart(sock, data)

        # M5
        data = (sock.recv(1000))
        logging.debug("---M5--->\n" + data)
        s_data = 'RTSP/1.0 200 OK\r\nCSeq: 4\r\n\r\n'
        logging.debug("<--------\n" + s_data)
        sock.sendall(s_data)

        # M6
        m6req = 'SETUP rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n' \
                + 'CSeq: 101\r\n' \
                + 'Transport: RTP/AVP/UDP;unicast;client_port=1028\r\n\r\n'
        logging.debug("<---M6---\n" + m6req)
        sock.sendall(m6req)
        data = (sock.recv(1000))
        logging.debug("-------->\n" + data)

        paralist = data.split(';')
        logging.debug(paralist)
        serverport = [x for x in paralist if 'server_port=' in x]
        logging.debug(serverport)
        serverport = serverport[-1]
        serverport = serverport[12:17]
        logging.debug(serverport)

        paralist = data.split()
        position = paralist.index('Session:') + 1
        sessionid = paralist[position]

        # M7
        m7req = 'PLAY rtsp://192.168.101.80/wfd1.0/streamid=0 RTSP/1.0\r\n' \
                + 'CSeq: 102\r\n' \
                + 'Session: ' + str(sessionid) + '\r\n\r\n'
        logging.debug("<---M7---\n" + m7req)
        sock.sendall(m7req)
        data = (sock.recv(1000))
        logging.debug("-------->\n" + data)
        logging.debug("---- Negotiation successful ----")

        if (os.uname()[-1][:4] != "armv"):
            player_select = 0
        else:
            player_select = Settings.player_select
        self.launchplayer(player_select)

        fcntl.fcntl(sock, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(idrsock, fcntl.F_SETFL, os.O_NONBLOCK)

        csnum = 102
        watchdog = 0
        while True:
            try:
                data = (sock.recv(1000))
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    try:
                        dontcare = (idrsock.recv(1000))
                    except socket.error as e:
                        err = e.args[0]
                        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                            sleep(0.01)
                            watchdog = watchdog + 1
                            if watchdog == 70 / 0.01:
                                self.pkill(['control.bin', 'controlhidc.bin', 'vlc', 'player.bin', 'h264.bin'])
                                sleep(1)
                                break
                        else:
                            sys.exit(1)
                    else:
                        csnum = csnum + 1
                        msg = 'wfd-idr-request\r\n'
                        idrreq = 'SET_PARAMETER rtsp://localhost/wfd1.0 RTSP/1.0\r\n' \
                                 + 'Content-Length: ' + str(len(msg)) + '\r\n' \
                                 + 'Content-Type: text/parameters\r\n' \
                                 + 'CSeq: ' + str(csnum) + '\r\n\r\n' \
                                 + msg
                        logging.debug(idrreq)
                        sock.sendall(idrreq)

                else:
                    sys.exit(1)
            else:
                logging.debug(data)
                watchdog = 0
                if len(data) == 0 or 'wfd_trigger_method: TEARDOWN' in data:
                    self.pkill(['control.bin', 'controlhidc.bin', 'vlc', 'player.bin', 'h264.bin'])
                    sleep(1)
                    break
                elif 'wfd_video_formats' in data:
                    self.launchplayer(player_select)
                messagelist = data.split('\r\n\r\n')
                logging.debug(messagelist)
                singlemessagelist = [x for x in messagelist if ('GET_PARAMETER' in x or 'SET_PARAMETER' in x)]
                logging.debug(singlemessagelist)
                for singlemessage in singlemessagelist:
                    entrylist = singlemessage.split('\r')
                    for entry in entrylist:
                        if 'CSeq' in entry:
                            cseq = entry
                    resp = 'RTSP/1.0 200 OK\r' + cseq + '\r\n\r\n';  # cseq contains \n
                    logging.debug(resp)
                    sock.sendall(resp)
                self.uibcstart(sock, data)
        idrsock.close()
        sock.close()


class LazyCast():

    def __init__(self):
        self.wpalib = WpaLib()

    def start_udhcpd(self, interface):
        tmpdir = tempfile.mkdtemp()
        conf = "start  192.168.173.80\nend 192.168.173.80\ninterface {}\noption subnet 255.255.255.0\noption lease 60\n".format(interface)
        conf_path = os.path.join(tmpdir, "udhcpd.conf")
        with open(conf_path, 'w') as c:
            c.write(conf)
        self.udhcpd_pid = subprocess.Popen(["sudo", "udhcpd", conf_path])

    def start_wifi_p2p(self):
        if self.wpalib.check_p2p():
            logging.info("Already on;")
        else:
            wpacli = WpaCli()
            wpacli.start_p2p_find()
            wpacli.set_device_name("lazycast")
            wpacli.set_device_type("7-0050F204-1")
            wpacli.set_p2p_go_ht40()
            wpacli.wfd_subelem_set("0 00060151022a012c")
            wpacli.wfd_subelem_set("1 0006000000000000")
            wpacli.wfd_subelem_set("6 000700000000000000")
            # fixme: detect existent persisntent group and use it
            # perentry="$(wpa_cli list_networks | grep "\[DISABLED\]\[P2P-PERSISTENT\]" | tail -1)"
		    # networkid=${perentry%%D*}
            wpacli.p2p_group_add("persistent")

    def run(self):
        self.start_wifi_p2p()
        p2p_interface = self.wpalib.get_p2p_interface()
        os.system("sudo ifconfig {} 192.168.173.1".format(p2p_interface))
        self.start_udhcpd(p2p_interface)
        d2 = D2()
        wpacli = WpaCli()
        while(True):
            wpacli.set_wps_pin(p2p_interface, "12345678", 300)
            d2.run()
