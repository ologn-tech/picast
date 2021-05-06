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
import subprocess
import tempfile
from logging import getLogger

from .settings import Settings


class Dhcpd:
    """DHCP server daemon running in background."""

    def __init__(self, interface: str, logger="picast"):
        """Constructor accept an interface to listen."""
        self.config = Settings()
        self.dhcpd = None
        self.interface = interface
        self.logger = getLogger(logger)
        self.conf_path = self._create_conf()

    def _create_conf(self):
        fd, conf_path = tempfile.mkstemp(suffix=".conf")
        conf = "start  {}\nend {}\ninterface {}\nnotify_file dumpleases\noption subnet {}\noption lease {}\n".format(
            Settings().peeraddress, Settings().peeraddress, self.interface, Settings().netmask, Settings().timeout
        )
        with open(conf_path, "w") as c:
            c.write(conf)
        return conf_path

    def start(self):
        self.logger.debug("Start dhcpd server.")
        self.dhcpd = subprocess.Popen(
            ["sudo", "udhcpd", "-f", self.conf_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = (None, None)
        try:
            out, err = self.dhcpd.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        self.logger.debug("udhcpd return code: {}".format(self.dhcpd.returncode))
        self.logger.debug("udhcpd stdout: {}".format(out))
        self.logger.debug("udhcpd stderr: {}".format(err))
        if self.dhcpd.returncode is not None and self.dhcpd.returncode != 0:
            self.logger.fatal(
                "Failed to start udhcp, please check debug for reasons, e.g. port is in use by dnsmsq or something ..."
            )
            os._exit(1)

    def stop(self):
        if self.dhcpd is not None:
            self.dhcpd.terminate()
            os.unlink(self.conf_path)
            # FIXME: workaround for sudo process killing.
            os.system("sudo pkill udhcpd")
