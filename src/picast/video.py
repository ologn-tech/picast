#!/usr/bin/env python3

"""
picast - a simple wireless display receiver for Raspberry Pi

    Copyright (C) 2019-2022 Hiroshi Miura
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

import json
import os
import subprocess
from logging import getLogger
from typing import Dict, List

from .settings import Settings


class GenericVideo:
    def __init__(self):
        self.native = 0x06  # type: int
        self.preferred = 0  # type: int
        self.profile = 0x01  # type: int
        self.level = 0x10  # type: int
        self.cea = 0x00FFFFFF  # type: int
        self.vesa = 0x00FFFFFF  # type: int
        self.hh = 0x00FF  # type: int

    def get_wfd_video_formats(self) -> str:
        return "{0:02X} {1:02X} {2:02X} {3:02X} {4:08X} {5:08X} {6:08X} 00 0000 0000 00 none none".format(
            self.native, self.preferred, self.profile, self.level, self.cea, self.vesa, self.hh
        )


class RasberryPiVideo:
    """Video parameters from Raspberry Pi specific command."""

    def __init__(self):
        self.config = Settings()
        self.native = 0x06
        self.preferred = 0
        self.profile = 0x01
        self.level = 0x10
        with open(os.path.join(os.path.dirname(__file__), "resolutions.json"), "r") as j:
            self.resolutions = json.load(j)[0]
        self._get_display_resolutions()

    def get_wfd_video_formats(self) -> str:
        return "{0:02X} {1:02X} {2:02X} {3:02X} {4:08X} {5:08X} {6:08X} 00 0000 0000 00 none none".format(
            self.native, self.preferred, self.profile, self.level, self.cea, self.vesa, self.hh
        )

    def _retrieve_mode(self) -> List[Dict[str, str]]:
        logger = getLogger(self.config.logger)
        status = []  # type: List[Dict[str, str]]
        data = subprocess.Popen("/usr/bin/modetest", stdout=subprocess.PIPE).communicate()[0].decode("UTF-8")
        modeline = False
        for line in data.splitlines():
            if "modes:" in line:
                modeline = True
            if not modeline:
                continue
            if "props:" in line:
                break
            if line.startswith("#"):
                entries = line.split(" ")
                status.append({"width": entries[3], "height": entries[7], "rate": entries[2]})
                logger.info("Added {}x{}x{}".format(entries[3], entries[7], entries[2]))
        return status

    def _get_display_resolutions(self) -> None:
        cea = 0x01
        vesa = 0x00
        hh = 0x00
        modes = self._retrieve_mode()  # type: List[Dict[str, str]]
        for r in modes:
            res_list = self.resolutions["cea"]
            for res in res_list:
                if res["mode"] == r["code"]:
                    cea |= 1 << res["id"]
                    break
        for r in modes:
            res_list = self.resolutions["vesa"]
            for res in res_list:
                if res["mode"] == r["code"]:
                    vesa |= 1 << res["id"]
                    break
        self.cea = cea
        self.vesa = vesa
        self.hh = hh
