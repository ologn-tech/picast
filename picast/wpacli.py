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

import re
import subprocess
from logging import getLogger
from typing import List, Optional, Tuple

from picast.exceptions import WpaException


class WpaCli:
    """
    Wraps the wpa_cli command line interface.
    """

    def __init__(self, logger='picast'):
        self.logger = getLogger(logger)
        pass

    def cmd(self, *argv):
        p = subprocess.Popen(["sudo", "wpa_cli"] + list(argv), stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        return stdout.decode('UTF-8').splitlines()

    def start_p2p_find(self):
        self.logger.debug("wpa_cli p2p_find type=progressive")
        status = self.cmd("p2p_find", "type=progressive")
        if 'OK' not in status:
            raise WpaException("Fail to start p2p find.")

    def stop_p2p_find(self):
        self.logger.debug("wpa_cli p2p_stop_find")
        status = self.cmd("p2p_stop_find")
        if 'OK' not in status:
            raise WpaException("Fail to stop p2p find.")

    def set_device_name(self, name: str):
        self.logger.debug("wpa_cli set device_name {}".format(name))
        status = self.cmd("set", "device_name", name)
        if 'OK' not in status:
            raise WpaException("Fail to set device name {}".format(name))

    def set_device_type(self, type):
        self.logger.debug("wpa_cli set device_type {}".format(type))
        status = self.cmd("set", "device_type", type)
        if 'OK' not in status:
            raise WpaException("Fail to set device type {}".format(type))

    def set_p2p_go_ht40(self):
        self.logger.debug("wpa_cli set p2p_go_ht40 1")
        status = self.cmd("set", "p2p_go_ht40", "1")
        if 'OK' not in status:
            raise WpaException("Fail to set p2p_go_ht40")

    def wfd_subelem_set(self, key: int, val: str):
        self.logger.debug("wpa_cli wfd_subelem_set {0:d} {1:s}".format(key, val))
        status = self.cmd("wfd_subelem_set", "{0:d}".format(key), val)
        if 'OK' not in status:
            raise WpaException("Fail to wfd_subelem_set.")

    def p2p_group_add(self, name: str):
        self.logger.debug("wpa_cli p2p_group_add {}".format(name))
        self.cmd("p2p_group_add", name)

    def set_wps_pin(self, interface: str, pin: str, timeout: int):
        self.logger.debug("wpa_cli -i {0:s} wps_pin any {1:s} {2:d}".format(interface, pin, timeout))
        status = self.cmd("-i", interface, "wps_pin", "any", "{0:s}".format(pin), "{0:d}".format(timeout))
        return status

    def get_interfaces(self) -> Tuple[str, List[str]]:
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

    def get_p2p_interface(self) -> Optional[str]:
        sel, interfaces = self.get_interfaces()
        for it in interfaces:
            if it.startswith("p2p-wl"):
                return it
        return None

    def check_p2p_interface(self) -> bool:
        if self.get_p2p_interface() is not None:
            return True
        return False
