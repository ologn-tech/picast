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

import os
from logging import getLogger
from time import sleep

from . import PiCastException
from .settings import Settings
from .wpacli import WpaCli
from .dhcpd import Dhcpd


class WifiP2PServer:

    def start(self):
        self.set_p2p_interface()
        self.start_dhcpd()
        self.start_wps()

    def start_wps(self):
        wpacli = WpaCli()
        wpacli.set_wps_pin(self.wlandev, Settings.pin, Settings.timeout)

    def start_dhcpd(self):
        dhcpd = Dhcpd(self.wlandev)
        dhcpd.start()
        sleep(0.5)

    def wfd_devinfo(self):
        type = 0b01  # PRIMARY_SINK
        session = 0b01 << 4
        wsd = 0b01 << 6
        pc = 0b00  # = P2P
        cp_support = 0b01 << 8
        ts = 0b00
        devinfo = type | session | wsd | pc | cp_support | ts
        control = 554  # Settings.rtsp_port
        max_tp = 300  # Mbps
        return '0006{0:04x}{1:04x}{2:04x}'.format(devinfo, control, max_tp)

    def wfd_bssid(self, bssid):
        return '0006{0:012x}'.format(bssid)

    def wfd_sink_info(self, status, mac):
        return '0007{0:02x}{1:012x}'.format(status, mac)

    def create_p2p_interface(self):
        wpacli = WpaCli()
        wpacli.start_p2p_find()
        wpacli.set_device_name(Settings.wp_device_name)
        wpacli.set_device_type(Settings.wp_device_type)
        wpacli.set_p2p_go_ht40()
        wpacli.wfd_subelem_set(0, self.wfd_devinfo())
        wpacli.wfd_subelem_set(1, self.wfd_bssid(0))
        wpacli.wfd_subelem_set(6, self.wfd_sink_info(0, 0))
        wpacli.p2p_group_add(Settings.wp_group_name)

    def set_p2p_interface(self):
        logger = getLogger("PiCast")
        wpacli = WpaCli()
        if wpacli.check_p2p_interface():
            logger.info("Already set a p2p interface.")
            p2p_interface = wpacli.get_p2p_interface()
        else:
            self.create_p2p_interface()
            sleep(3)
            p2p_interface = wpacli.get_p2p_interface()
            if p2p_interface is None:
                raise PiCastException("Can not create P2P Wifi interface.")
            logger.info("Start p2p interface: {}".format(p2p_interface))
            os.system("sudo ifconfig {} {}".format(p2p_interface, Settings.myaddress))
        self.wlandev = p2p_interface
