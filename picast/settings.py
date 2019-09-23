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

import configparser
import os
import threading


class Settings():
    # this class is Borg/Singleton
    _shared_state = {
        '_config': None,
        '_lock': threading.Lock()
    }

    def __new__(cls, *p, **k):
        self = object.__new__(cls, *p, **k)
        self.__dict__ = cls._shared_state
        return self

    def __init__(self, config=None):
        if self._config is None:
            with self._lock:
                if self._config is None:
                    if config is None:
                        inidir = os.path.dirname(__file__)
                        inifile = os.path.join(inidir, 'settings.ini')
                    else:
                        inidir = os.path.dirname(config)
                        inifile = config
                    self._config = self.configParse(inifile)

    def configParse(self, file_path) :
        if not os.path.exists(file_path) :
            raise IOError(file_path)
        config = configparser.ConfigParser()
        config.read(file_path)
        return config

    @property
    def logging_config(self):
        return self._config.get('logging', 'config')

    @property
    def logger(self):
        return self._config.get('logging', 'logger')

    @property
    def rtp_port(self):
        return self._config.getint('network', 'rtp_port')

    @property
    def myaddress(self):
        return self._config.get('network', 'myaddress')

    @property
    def peeraddress(self):
        return self._config.get('network', 'peeraddress')

    @property
    def netmask(self):
        return self._config.get('network', 'netmask')

    @property
    def pin(self):
        return self._config.get('p2p', 'pin')

    @property
    def timeout(self):
        return self._config.getint('p2p', 'timeout')

    @property
    def group_name(self):
        return self._config.get('p2p', 'group_name')

    @property
    def device_type(self):
        return self._config.get('p2p', 'device_type')

    @property
    def device_name(self):
        return self._config.get('p2p', 'device_name')

    @property
    def rtsp_port(self):
        return self._config.getint('network', 'rtsp_port')
