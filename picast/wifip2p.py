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
import threading
from logging import getLogger
from time import sleep

from picast.dhcpd import Dhcpd
from picast.exceptions import WpaException
from picast.settings import Settings
from picast.wpacli import WpaCli


class WifiP2PServer(threading.Thread):

    def __init__(self, R2=False, logger='picast'):
        super(WifiP2PServer, self).__init__(name='wifi-p2p-0', daemon=False)
        self.config = Settings()
        self.logger = getLogger(logger)
        self.set_p2p_interface(R2)

    def run(self):
        self.start_dhcpd()
        self.start_wps()

    def start_wps(self):
        wpacli = WpaCli()
        wpacli.set_wps_pin(self.wlandev, self.config.pin, self.config.timeout)

    def start_dhcpd(self):
        dhcpd = Dhcpd(self.wlandev)
        dhcpd.start()

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

    def wfd_bssid(self, bssid: int) -> str:
        return '0006{0:012X}'.format(bssid)

    def wfd_sink_info(self, status: int, mac: int) -> str:
        return '0007{0:02X}{1:012X}'.format(status, mac)

    def wfd_ext_cap(self, uibc=False, i2c=False) -> str:
        val_uibc = 0b1 if uibc else 0b0
        val_i2c = (0b1 if i2c else 0b0) << 1
        val = val_uibc | val_i2c
        return '0002{0:04X}'.format(val)

    def wfd_devinfo2(self) -> str:
        r2_sink = 0b01
        return '0002{0:04X}'.format(r2_sink)

    def create_p2p_interface(self, R2):
        wpacli = WpaCli()
        wpacli.start_p2p_find()
        wpacli.set_device_name(self.config.device_name)
        wpacli.set_device_type(self.config.device_type)
        wpacli.set_p2p_go_ht40()
        wpacli.wfd_subelem_set(0, self.wfd_devinfo())
        wpacli.wfd_subelem_set(1, self.wfd_bssid(0))
        wpacli.wfd_subelem_set(6, self.wfd_sink_info(0, 0))
        wpacli.wfd_subelem_set(7, self.wfd_ext_cap(uibc=False, i2c=False))
        if R2:
            wpacli.wfd_subelem_set(11, self.wfd_devinfo2())
        wpacli.p2p_group_add(self.config.group_name)

    def set_p2p_interface(self, R2):
        wpacli = WpaCli()
        if wpacli.check_p2p_interface():
            self.logger.info("Already set a p2p interface.")
            p2p_interface = wpacli.get_p2p_interface()
        else:
            self.create_p2p_interface(R2)
            sleep(3)
            p2p_interface = wpacli.get_p2p_interface()
            if p2p_interface is None:
                raise WpaException("Can not create P2P Wifi interface.")
            self.logger.info("Start p2p interface: {} address {}".format(p2p_interface, self.config.myaddress))
            os.system("sudo ifconfig {} {}".format(p2p_interface, self.config.myaddress))
        self.wlandev = p2p_interface
