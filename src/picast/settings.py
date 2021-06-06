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
import enum
import os
import shlex
import threading


class PlatformType(enum.Enum):
    RaspberryPi = 1
    BeagleBoardBlack = 2
    PandaBoard = 3
    Generic = 999


class Settings(object):
    # this class is Borg/Singleton
    _shared_state = {"_config": None, "_lock": threading.Lock()}

    def __init__(self, config=None):
        self.__dict__ = self._shared_state
        if self._config is None:
            with self._lock:
                if self._config is None:
                    if config is None:
                        inidir = os.path.dirname(__file__)
                        self.inifile = os.path.join(inidir, "settings.ini")
                    else:
                        inidir = os.path.dirname(config)
                        self.inifile = config
                    self._config = self.configParse(self.inifile)
                    self._platform = self._detect_platform()

    def configParse(self, file_path):
        if not os.path.exists(file_path):
            raise IOError(file_path)
        config = configparser.ConfigParser()
        config.read(file_path)
        return config

    def _detect_platform(self):
        self.platform = PlatformType.RaspberryPi  # FIXME

    def get_wfd_parameters(self):
        return self._config["wfd_parameter"]

    @property
    def logging_config(self):
        return self._config.get("logging", "config")

    @property
    def logger(self):
        return self._config.get("logging", "logger")

    @property
    def player(self):
        return self._config.get("player", "name")

    @property
    def player_log_file(self):
        return self._config.get("player", "log_file")

    @property
    def player_custom_args(self):
        return shlex.split(self._config.get("player", "custom_args"))

    @property
    def rtp_port(self):
        return self._config.getint("network", "rtp_port")

    @property
    def myaddress(self):
        return self._config.get("network", "myaddress")

    @property
    def peeraddress(self):
        return self._config.get("network", "peeraddress")

    @property
    def netmask(self):
        return self._config.get("network", "netmask")

    @property
    def wps_mode(self):
        return self._config.get("p2p", "wps_mode")

    @property
    def pin(self):
        return self._config.get("p2p", "pin")

    @property
    def timeout(self):
        return self._config.getint("p2p", "timeout")

    @property
    def group_name(self):
        return self._config.get("p2p", "group_name")

    @property
    def device_type(self):
        return self._config.get("p2p", "device_type")

    @property
    def device_name(self):
        return self._config.get("p2p", "device_name")

    @property
    def rtsp_port(self):
        return self._config.getint("network", "rtsp_port")

    @property
    def gst_decoder(self):
        return self._config.get("gst", "decoder")

    @property
    def max_timeout(self):
        return self._config.get("network", "max_timeout")
