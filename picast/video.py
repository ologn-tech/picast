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
from typing import List, Tuple, Optional

from picast.settings import Settings


class Res:

    def __init__(self, width:int, height:int, refresh:int, progressive:bool=True, h264level:str='3.1', h265level:str='3.1'):
        self.width = width
        self.height = height
        self.refresh = refresh
        self.progressive = progressive
        self.h264level = h264level
        self.h265level = h265level

    @property
    def score(self) -> int:
        return self.width * self.height * self.refresh * (1 + 1 if self.progressive else 0)

    def __repr__(self):
        return "%s(%d,%d,%d,%s)" % (type(self).__name__, self.width, self.height, self.refresh,
                                       'p' if self.progressive else 'i')

    def __str__(self):
        return 'resolution %d x %d x %d%s' % (self.width, self.height, self.refresh,
                                                  'p' if self.progressive else 'i')

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __ne__(self, other):
        return repr(self) != repr(other)

    def __ge__(self, other):
        return self.score >= other.score

    def __gt__(self, other):
        return self.score > other.score

    def __le__(self, other):
        return self.score <= other.score

    def __lt__(self, other):
        return self.score < other.score


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

    resolutions = {}

    def __init__(self, *args):
        for r in args:
            if r[1] == 'cea' or r[1] == 'vesa' or r[1] == 'hh':
                    self.resolutions[r[0]] = {r[1]: r[2], 'hdmi': HdmiMode(r[3], r[4])}
            else:
                raise ValueError('Unknown resolution type.')

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
        self.resolutions = ResolutionSet([
            # (res, (cea or vesa), hdmi_mode(vesa), hdmi(cea)
            (Res(640, 480, 60, True), 'cea', 0, 4, 1),
            (Res(720, 480, 60, True), 'cea', 1, None, 3),
            (Res(720, 480, 60, False), 'cea', 2, None, 7),
            (Res(720, 480, 50, True), 'cea', 3, None, None),
            (Res(720, 576, 50, False), 'cea', 4, None, 17),
            (Res(1280, 720, 30, True), 'cea', 5, None, None),
            (Res(1280, 720, 60, True, '3.2', '4'), 'cea', 6, None, 4),
            (Res(1280, 1080, 30, True, '4', '4'), 'cea', 7, None, 34),
            (Res(1920, 1080, 60, True, '4.2', '4.1'), 'cea', 8, None, 16),
            (Res(1920, 1080, 60, False, '4', '4'), 'cea', 9, None, 5),
            (Res(1280,  720, 25, True), 'cea', 10, None, None),
            (Res(1280,  720, 50, True, '3.2', '4'), 'cea', 11, None, 19),
            (Res(1920, 1080, 25, True, '3.2', '4'), 'cea', 12, None, None),
            (Res(1920, 1080, 50, True, '4.2', '4.1'), 'cea', 13, None, 31),
            (Res(1920, 1080, 50, False, '3.2', '4'), 'cea', 14, None, 20),
            (Res(1280,  720, 24, True), 'cea', 15, None, None),
            (Res(1920, 1080, 24, True, '3.2', '4'), 'cea', 16, None, 32),
            (Res(3840, 2160, 30, True, '5.1', '5'), 'cea', 17, None, None),
            (Res(3840, 2160, 60, True, '5.1', '5'), 'cea', 18, None, None),
            (Res(4096, 2160, 30, True, '5.1', '5'), 'cea', 19, None, None),
            (Res(4096, 2160, 60, True, '5.2', '5.1'), 'cea', 20, None, None),
            (Res(3840, 2160, 25, True, '5.2', '5.1'), 'cea', 21, None, None),
            (Res(3840, 2160, 50, True, '5.2', '5'), 'cea', 22, None, None),
            (Res(4096, 2160, 25, True, '5.2', '5'), 'cea', 23, None, None),
            (Res(4086, 2160, 50, True, '5.2', '5'), 'cea', 24, None, None),
            (Res(4096, 2160, 24, True, '5.2', '5.1'), 'cea', 25, None, None),
            (Res(4096, 2160, 24, True, '5.2', '5.1'), 'cea', 26, None, None),
            (Res(800,  600, 30, True, '3.1', '3.1'), 'vesa', 0, None, None),
            (Res(800,  600, 60, True, '3.2', '4'),'vesa', 1, 9, None),
            (Res(1024,  768, 30, True, '3.1', '3.1'), 'vesa', 2, 16, None),
            (Res(1024,  768, 60, True, '3.2', '4'), 'vesa', 3, None, None),
            (Res(1152,  854, 30, True, '3.2', '4'), 'vesa', 4, None, None),
            (Res(1152,  854, 60, True, '4', '4.1'), 'vesa', 5, None, None),
            (Res(1280,  768, 30, True, '3.2', '4'), 'vesa', 6, None, None),
            (Res(1280,  768, 60, True, '4', '4.1'), 'vesa', 7, None, None),
            (Res(1280,  800, 30, True, '3.2', '4'), 'vesa', 8, None, None),
            (Res(1280,  800, 60, True, '4', '4.1'), 'vesa', 9, None, None),
            (Res(1360,  768, 30, True, '3.2', '4'), 'vesa', 10, None, None),
            (Res(1360,  768, 60, True, '4', '4.1'), 'vesa', 11, 39, None),
            (Res(1366,  768, 30, True, '3.2', '4'), 'vesa', 12, None, None),
            (Res(1366,  768, 60, True, '4.2', '4.1'), 'vesa', 13, None, None),
            (Res(1280, 1024, 30, True, '3.2', '4'), 'vesa', 14, None, None),
            (Res(1280, 1024, 60, True, '4.2', '4.1'), 'vesa', 15, 35, None),
            (Res(1440, 1050, 30, True, '3.2', '4'), 'vesa', 16, None, None),
            (Res(1440, 1050, 60, True, '4.2', '4.1'), 'vesa', 17, None, None),
            (Res(1440,  900, 30, True, '3.2', '4'), 'vesa', 18, None, None),
            (Res(1440,  900, 60, True, '4.2', '4.1'), 'vesa', 19, 47, None),
            (Res(1600,  900, 30, True, '3.2', '4'), 'vesa', 20, None, None),
            (Res(1600,  900, 60, True, '4.2', '4.1'), 'vesa', 21, 83, None),
            (Res(1600, 1200, 30, True, '4', '5'), 'vesa', 22, None, None),
            (Res(1600, 1200, 60, True, '4.2', '5.1'), 'vesa', 23, 51, None),
            (Res(1680, 1024, 30, True, '3.2', '4'), 'vesa', 24, None, None),
            (Res(1680, 1024, 60, True, '4.2', '4.1'),'vesa', 25, None, None),
            (Res(1680, 1050, 30, True, '3.2', '4'), 'vesa', 26, None, None),
            (Res(1680, 1050, 60, True, '4.2', '4.1'), 'vesa', 27, 58, None),
            (Res(1920, 1200, 30, True, '4.2', '5'), 'vesa', 28, None, None),
            (Res(800, 400, 30), 'hh', 0, None, None),
            (Res(800, 480, 60), 'hh', 1, None, None),
            (Res(854, 480, 30), 'hh', 2, None, None),
            (Res(854, 480, 60), 'hh', 3, None, 3),
            (Res(864, 480, 30), 'hh', 4, None, None),
            (Res(864, 480, 60), 'hh', 5, None, None),
            (Res(640, 360, 30), 'hh', 6, None, None),
            (Res(640, 360, 60), 'hh', 7, None, None),
            (Res(960, 540, 30), 'hh', 8, None, None),
            (Res(960, 540, 60), 'hh', 9, None, None),
            (Res(848, 480, 30), 'hh', 10, None, None),
            (Res(848, 480, 60), 'hh', 11, None, None),
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
        logger = getLogger(Settings.logger)
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
