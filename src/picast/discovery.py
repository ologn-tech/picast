#!/usr/bin/env python3

"""
picast - a simple wireless display receiver for Raspberry Pi

    Copyright (C) 2019,2020 Hiroshi Miura
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

import socket
from logging import getLogger

import zeroconf

from .settings import Settings


class ServiceDiscovery():
    """Register and query mDNS/SD entries"""

    def __init__(self):
        self.config = Settings()
        self.logger = getLogger(self.config.logger)
        self.zc = zeroconf.Zeroconf()

    def register(self):
        service_info = zeroconf.ServiceInfo('_display._tcp.local.', 'PiCast Remote Display._display._tcp.local.',
                                            addresses=[socket.inet_aton(self.config.myaddress)], port=self.config.rtsp_port)
        self.zc.register_service(service_info, ttl=60, allow_name_change=False)
        self.logger.info("Register mDNS/SD entry.")

    def lookup(self):
        service_info = self.zc.get_service_info('_displaysrc._tcp.local.', None)
        return service_info.addresses, service_info.port
