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
from logging import getLogger

os.putenv("DISPLAY", ":0")  # noqa: E402 # isort:skip

from ..settings import Settings  # noqa: E402 # isort:skip


class VlcPlayer:
    def __init__(self, logger="picast"):
        self.config = Settings()
        self.logger = getLogger(logger)
        self.vlc = None

    def start(self):
        self.logger.debug("Start vlc client.")
        self.vlc = subprocess.Popen(
            [
                "cvlc",
                "--fullscreen",
                *self.config.player_custom_args,
                "--file-logging",
                "--logfile",
                self.config.player_log_file,
                "rtp://0.0.0.0:1028/wfd1.0/streamid=0",
            ]
        )

    def stop(self):
        if self.vlc is not None:
            self.logger.debug("Stop vlc client.")
            self.vlc.terminate()
