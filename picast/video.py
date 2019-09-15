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
import subprocess


class Res:

    def __init__(self, id, width, height, refresh, progressive=True, h264level='3.1', h265level='3.1'):
        self.id = id
        self.width = width
        self.height = height
        self.refresh = refresh
        self.progressive = progressive
        self.h264level = h264level
        self.h265level = h265level

    @property
    def score(self):
        return self.width * self.height * self.refresh * (1 + 1 if self.progressive else 0)

    def __repr__(self):
        return "%s(%d,%d,%d,%d,%s)" % (type(self).__name__, self.id, self.width, self.height, self.refresh,
                                       'p' if self.progressive else 'i')

    def __str__(self):
        return 'resolution(%d) %d x %d x %d%s' % (self.id, self.width, self.height, self.refresh,
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


class WfdVideoParameters:

    resolutions_cea = [
        Res(0,   640,  480, 60, True),
        Res(1,   720,  480, 60, True),
        Res(2,   720,  480, 60, False),
        Res(3,   720,  480, 50, True),
        Res(4,   720,  576, 50, False),
        Res(5,  1280,  720, 30, True),
        Res(6,  1280,  720, 60, True, '3.2', '4'),
        Res(7,  1280, 1080, 30, True, '4', '4'),
        Res(8,  1920, 1080, 60, True, '4.2', '4.1'),
        Res(9,  1920, 1080, 60, False, '4', '4'),
        Res(10, 1280,  720, 25, True),
        Res(11, 1280,  720, 50, True, '3.2', '4'),
        Res(12, 1920, 1080, 25, True, '3.2', '4'),
        Res(13, 1920, 1080, 50, True, '4.2', '4.1'),
        Res(14, 1920, 1080, 50, False, '3.2', '4'),
        Res(15, 1280,  720, 24, True),
        Res(16, 1920, 1080, 24, True, '3.2', '4'),
        Res(17, 3840, 2160, 30, True, '5.1', '5'),
        Res(18, 3840, 2160, 60, True, '5.1', '5'),
        Res(19, 4096, 2160, 30, True, '5.1', '5'),
        Res(20, 4096, 2160, 60, True, '5.2', '5.1'),
        Res(21, 3840, 2160, 25, True, '5.2', '5.1'),
        Res(22, 3840, 2160, 50, True, '5.2', '5'),
        Res(23, 4096, 2160, 25, True, '5.2', '5'),
        Res(24, 4086, 2160, 50, True, '5.2', '5'),
        Res(25, 4096, 2160, 24, True, '5.2', '5.1'),
        Res(26, 4096, 2160, 24, True, '5.2', '5.1'),
    ]

    resolutions_vesa = [
        Res(0,   800,  600, 30, True, '3.1', '3.1'),
        Res(1,   800,  600, 60, True, '3.2', '4'),
        Res(2,  1024,  768, 30, True, '3.1', '3.1'),
        Res(3,  1024,  768, 60, True, '3.2', '4'),
        Res(4,  1152,  854, 30, True, '3.2', '4'),
        Res(5,  1152,  854, 60, True, '4', '4.1'),
        Res(6,  1280,  768, 30, True, '3.2', '4'),
        Res(7,  1280,  768, 60, True, '4', '4.1'),
        Res(8,  1280,  800, 30, True, '3.2', '4'),
        Res(9,  1280,  800, 60, True, '4', '4.1'),
        Res(10, 1360,  768, 30, True, '3.2', '4'),
        Res(11, 1360,  768, 60, True, '4', '4.1'),
        Res(12, 1366,  768, 30, True, '3.2', '4'),
        Res(13, 1366,  768, 60, True, '4.2', '4.1'),
        Res(14, 1280, 1024, 30, True, '3.2', '4'),
        Res(15, 1280, 1024, 60, True, '4.2', '4.1'),
        Res(16, 1440, 1050, 30, True, '3.2', '4'),
        Res(17, 1440, 1050, 60, True, '4.2', '4.1'),
        Res(18, 1440,  900, 30, True, '3.2', '4'),
        Res(19, 1440,  900, 60, True, '4.2', '4.1'),
        Res(20, 1600,  900, 30, True, '3.2', '4'),
        Res(21, 1600,  900, 60, True, '4.2', '4.1'),
        Res(22, 1600, 1200, 30, True, '4', '5'),
        Res(23, 1600, 1200, 60, True, '4.2', '5.1'),
        Res(24, 1680, 1024, 30, True, '3.2', '4'),
        Res(25, 1680, 1024, 60, True, '4.2', '4.1'),
        Res(26, 1680, 1050, 30, True, '3.2', '4'),
        Res(27, 1680, 1050, 60, True, '4.2', '4.1'),
        Res(28, 1920, 1200, 30, True, '4.2', '5'),
    ]

    resolutions_hh = [
        Res(0, 800, 400, 30),
        Res(1, 800, 480, 60),
        Res(2, 854, 480, 30),
        Res(3, 854, 480, 60),
        Res(4, 864, 480, 30),
        Res(5, 864, 480, 60),
        Res(6, 640, 360, 30),
        Res(7, 640, 360, 60),
        Res(8, 960, 540, 30),
        Res(9, 960, 540, 60),
        Res(10, 848, 480, 30),
        Res(11, 848, 480, 60),
    ]

    def get_video_parameter(self):
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
        native = 0x08
        preferred = 0
        profile = 0x02 | 0x01
        level = 0x10
        cea = 0x0001FFFF
        vesa = 0x0FFFFFFF
        handheld = 0x0
        msg += 'wfd_video_formats: {0:02X} {1:02X} {2:02X} {3:02X} {4:08X} {5:08X} {6:08X} 00 0000 0000 00 none none\r\n' \
               .format(native, preferred, profile, level, cea, vesa, handheld)
        msg += 'wfd_3d_video_formats: none\r\nwfd_coupled_sink: none\r\nwfd_display_edid: none\r\nwfd_connector_type: 05\r\n'
        msg += 'wfd_uibc_capability: none\r\nwfd_standby_resume_capability: none\r\nwfd_content_protection: none\r\n'
        return msg


    def get_display_resolutions(self):
        output = subprocess.Popen("xrandr | egrep -oh '[0-9]+x[0-9]+'", shell=True, stdout=subprocess.PIPE).communicate()[0]
        resolutions = output.split()
        return resolutions
