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
import re
import subprocess
from logging import getLogger
from typing import Tuple, Optional

from picast.settings import Settings


class HdmiMode:

    def __init__(self, vesa, cea):
        if vesa is None and cea is None:
            self.group = None
            self.mode = None
        elif vesa is None:
            self.group = 'cea'
            self.mode = cea
        elif cea is None:
            self.group = 'vesa'
            self.mode = vesa
        else:  # priority on vesa
            self.group = 'vesa'
            self.mode = vesa


class ResolutionSet:

    resolutions = []

    def __init__(self, args):
        for r in args:
            if r[4] == 'cea' or r[4] == 'vesa' or r[4] == 'hh':
                    self.resolutions.append({'width': r[0], 'height': r[1], 'rate': r[2], 'p': r[3],
                                             r[4]: r[5], 'hdmi': HdmiMode(r[6], r[7])})
            else:
                raise ValueError('Unknown resolution type. {}')

    def _get(self, mode, code) -> Optional[int]:
        for r in self.resolutions:
            if r['hdmi'] is not None:
                hdmi: HdmiMode = r['hdmi']
                if hdmi.group  == mode and hdmi.mode == code:
                    if mode in r:
                        return r[mode]
                    else:
                        return None
        return None

    def get_cea(self, code) -> Optional[int]:
        self._get('cea', code)

    def get_vesa(self, code) -> Optional[int]:
        self._get('vesa', code)


class WfdVideoParameters:

    def __init__(self):
        self.config = Settings()
        self.resolutions = ResolutionSet([
            (640, 480, 60, True, 'cea', 0, 4, 1),
            (720, 480, 60, True, 'cea', 1, None, 3),
            (720, 480, 60, False, 'cea', 2, None, 7),
            (720, 480, 50, True, 'cea', 3, None, None),
            (720, 576, 50, False, 'cea', 4, None, 17),
            (1280, 720, 30, True, 'cea', 5, None, None),
            (1280, 720, 60, True, 'cea', 6, None, 4),
            (1280, 1080, 30, True, 'cea', 7, None, 34),
            (1920, 1080, 60, True, 'cea', 8, None, 16),
            (1920, 1080, 60, False, 'cea', 9, None, 5),
            (1280,  720, 25, True, 'cea', 10, None, None),
            (1280,  720, 50, True, 'cea', 11, None, 19),
            (1920, 1080, 25, True, 'cea', 12, None, None),
            (1920, 1080, 50, True, 'cea', 13, None, 31),
            (1920, 1080, 50, False, 'cea', 14, None, 20),
            (1280,  720, 24, True, 'cea', 15, None, None),
            (1920, 1080, 24, True, 'cea', 16, None, 32),
            (3840, 2160, 30, True, 'cea', 17, None, None),
            (3840, 2160, 60, True, 'cea', 18, None, None),
            (4096, 2160, 30, True, 'cea', 19, None, None),
            (4096, 2160, 60, True, 'cea', 20, None, None),
            (3840, 2160, 25, True, 'cea', 21, None, None),
            (3840, 2160, 50, True, 'cea', 22, None, None),
            (4096, 2160, 25, True, 'cea', 23, None, None),
            (4086, 2160, 50, True, 'cea', 24, None, None),
            (4096, 2160, 24, True, 'cea', 25, None, None),
            (4096, 2160, 24, True, 'cea', 26, None, None),
            (800,  600, 30, True, 'vesa', 0, None, None),
            (800,  600, 60, True, 'vesa', 1, 9, None),
            (1024,  768, 30, True, 'vesa', 2, 16, None),
            (1024,  768, 60, True, 'vesa', 3, None, None),
            (1152,  854, 30, True, 'vesa', 4, None, None),
            (1152,  854, 60, True, 'vesa', 5, None, None),
            (1280,  768, 30, True, 'vesa', 6, None, None),
            (1280,  768, 60, True, 'vesa', 7, None, None),
            (1280,  800, 30, True, 'vesa', 8, None, None),
            (1280,  800, 60, True, 'vesa', 9, None, None),
            (1360,  768, 30, True, 'vesa', 10, None, None),
            (1360,  768, 60, True, 'vesa', 11, 39, None),
            (1366,  768, 30, True, 'vesa', 12, None, None),
            (1366,  768, 60, True, 'vesa', 13, None, None),
            (1280, 1024, 30, True, 'vesa', 14, None, None),
            (1280, 1024, 60, True, 'vesa', 15, 35, None),
            (1440, 1050, 30, True, 'vesa', 16, None, None),
            (1440, 1050, 60, True, 'vesa', 17, None, None),
            (1440,  900, 30, True, 'vesa', 18, None, None),
            (1440,  900, 60, True, 'vesa', 19, 47, None),
            (1600,  900, 30, True, 'vesa', 20, None, None),
            (1600,  900, 60, True, 'vesa', 21, 83, None),
            (1600, 1200, 30, True, 'vesa', 22, None, None),
            (1600, 1200, 60, True, 'vesa', 23, 51, None),
            (1680, 1024, 30, True, 'vesa', 24, None, None),
            (1680, 1024, 60, True, 'vesa', 25, None, None),
            (1680, 1050, 30, True, 'vesa', 26, None, None),
            (1680, 1050, 60, True, 'vesa', 27, 58, None),
            (1920, 1200, 30, True, 'vesa', 28, None, None),
            (800, 400, 30, True, 'hh', 0, None, None),
            (800, 480, 60, True, 'hh', 1, None, None),
            (854, 480, 30, True, 'hh', 2, None, None),
            (854, 480, 60, True, 'hh', 3, None, None),
            (864, 480, 30, True, 'hh', 4, None, None),
            (864, 480, 60, True, 'hh', 5, None, None),
            (640, 360, 30, True, 'hh', 6, None, None),
            (640, 360, 60, True, 'hh', 7, None, None),
            (960, 540, 30, True, 'hh', 8, None, None),
            (960, 540, 60, True, 'hh', 9, None, None),
            (848, 480, 30, True, 'hh', 10, None, None),
            (848, 480, 60, True, 'hh', 11, None, None)
        ])

    def get_video_parameter(self) -> str:
        # audio_codec: LPCM:0x01, AAC:0x02, AC3:0x04
        # audio_sampling_frequency: 44.1khz:1, 48khz:2
        # LPCM: 44.1kHz, 16b; 48 kHZ,16b
        # AAC: 48 kHz, 16b, 2 channels; 48kHz,16b, 4 channels, 48 kHz,16b,6 channels
        # AAC 00000001 00  : 2 ch AAC 48kHz
        msg = 'wfd_audio_codecs: AAC 00000001 00, LPCM 00000002 00\r\n'
        # wfd_video_formats: <native_resolution: 0x20>, <preferred>, <profile>, <level>,
        #                    <cea>, <vesa>, <hh>, <latency>, <min_slice>, <slice_enc>, <frame skipping support>
        #                    <max_hres>, <max_vres>
        # native: index in CEA support.
        # preferred-display-mode-supported: 0 or 1
        # profile: Constrained High Profile: 0x02, Constraint Baseline Profile: 0x01
        # level: H264 level 3.1: 0x01, 3.2: 0x02, 4.0: 0x04,4.1:0x08, 4.2=0x10
        #   3.2: 720p60,  4.1: FullHD@24, 4.2: FullHD@60
        native = 0x06
        preferred = 0
        profile = 0x02 | 0x01
        level = 0x02
        cea, vesa, hh = self.get_display_resolutions()
        msg += 'wfd_video_formats: {0:02X} {1:02X} {2:02X} {3:02X} {4:08X} {5:08X} {6:08X} 00 0000 0000 00 none none\r\n' \
               .format(native, preferred, profile, level, cea, vesa, hh)
        msg += 'wfd_3d_video_formats: none\r\nwfd_coupled_sink: none\r\nwfd_display_edid: none\r\nwfd_connector_type: 05\r\n'
        msg += 'wfd_uibc_capability: none\r\nwfd_standby_resume_capability: none\r\nwfd_content_protection: none\r\n'
        return msg

    class TvModes(enum.Enum):
        CEA = "-m CEA -j"
        DMT = "-m DMT -j"
        Current = "-s"

    def retrieve_tvservice(self, mode: TvModes) -> dict:
        logger = getLogger(self.config.logger)
        if mode is self.TvModes.Current:
            data = subprocess.Popen("tvservice -s", shell=True, stdout=subprocess.PIPE).communicate()[0]
            logger.debug("tvservice: {}".format(data))
            r = re.compile(r'([0-9]+)x([0-9]+),\s+@\s+([1-9][0-9])\.[0-9][0-9]HZ')
            m = r.match(data)
            status = {'width': m.group(1), 'height': m.group(2), 'rate': m.group(3)}
        elif mode is self.TvModes.CEA:
            data = subprocess.Popen("tvservice -m CEA -j", shell=True, stdout=subprocess.PIPE).communicate()[0]
            logger.debug("tvservice: {}".format(data))
            status = json.loads(data)
        else:
            data = subprocess.Popen("tvservice -m DMT -j", shell=True, stdout=subprocess.PIPE).communicate()[0]
            logger.debug("tvservice: {}".format(data))
            status = json.load(data)
        return status

    def get_display_resolutions(self) -> Tuple[int, int, int]:
        cea = 0x01
        vesa = 0x00
        hh =  0x00
        cea_resolutions = self.retrieve_tvservice(mode=self.TvModes.CEA)
        for r in cea_resolutions:
            cea = self.resolutions.get_cea(code=r['code'])
            if cea is not None:
                cea |= 1 << cea
        dmt_resolutions = self.retrieve_tvservice(mode=self.TvModes.DMT)
        for r in dmt_resolutions:
            dmt = self.resolutions.get_vesa(code=r['code'])
            if dmt is not None:
                vesa |= 1 << dmt
        return cea, vesa, hh
