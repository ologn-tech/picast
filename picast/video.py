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

import enum
import json
import os
import re
import subprocess
from logging import getLogger
from typing import Tuple

from picast.settings import Settings


class WfdVideoParameters:

    def __init__(self):
        self.config = Settings()
        with open(os.path.join(os.path.dirname(__file__), 'resolutions.json'), 'r') as j:
            self.resolutions = json.load(j)[0]

    def get_video_parameter(self) -> str:
        # wfd_video_formats: <native_resolution: 0x20>, <preferred>, <profile>, <level>,
        #                    <cea>, <vesa>, <hh>, <latency>, <min_slice>, <slice_enc>, <frame skipping support>
        #                    <max_hres>, <max_vres>
        # native: index in CEA support.
        # preferred-display-mode-supported: 0 or 1
        # profile: Constrained High Profile: 0x02, or Constraint Baseline Profile: 0x01, only one bit set
        # level: H264 level 3.1: 0x01, 3.2: 0x02, 4.0: 0x04,4.1:0x08, 4.2=0x10
        #   3.2: 720p60,  4.1: FullHD@24, 4.2: FullHD@60
        native = 0x06
        preferred = 0
        profile = 0x02
        level = 0x02
        cea, vesa, hh = self.get_display_resolutions()
        return '{0:02X} {1:02X} {2:02X} {3:02X} {4:08X} {5:08X} {6:08X} 00 0000 0000 00 none none' \
               .format(native, preferred, profile, level, cea, vesa, hh)

    class TvModes(enum.Enum):
        CEA = "-m CEA -j"
        DMT = "-m DMT -j"
        Current = "-s"

    def _call_tvservice(self, cmd):
        logger = getLogger(self.config.logger)
        data = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
        logger.debug("tvservice: {}".format(data))
        return data

    def retrieve_tvservice(self, mode: TvModes) -> dict:
        if mode is self.TvModes.Current:
            data = self._call_tvservice("tvservice -s")
            r = re.compile(r'([0-9]+)x([0-9]+),\s+@\s+([1-9][0-9])\.[0-9][0-9]HZ')
            m = r.match(data)
            status = {'width': m.group(1), 'height': m.group(2), 'rate': m.group(3)}
        elif mode is self.TvModes.CEA:
            data = self._call_tvservice("tvservice -m CEA -j")
            status = json.loads(data)
        else:
            data = self._call_tvservice("tvservice -m DMT -j")
            status = json.loads(data)
        return status

    def get_display_resolutions(self) -> Tuple[int, int, int]:
        cea = 0x01
        vesa = 0x00
        hh =  0x00
        cea_resolutions = self.retrieve_tvservice(mode=self.TvModes.CEA)
        for r in cea_resolutions:
            res_list = self.resolutions['cea']
            for res in res_list:
                if res['mode'] == r['code']:
                    cea |= 1 << res['id']
                    break
        dmt_resolutions = self.retrieve_tvservice(mode=self.TvModes.DMT)
        for r in dmt_resolutions:
            res_list = self.resolutions['vesa']
            for res in res_list:
                if res['mode'] == r['code']:
                    vesa |= 1 << res['id']
                    break
        return cea, vesa, hh
