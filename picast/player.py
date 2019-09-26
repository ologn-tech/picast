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

import gi

os.putenv('DISPLAY', ':0')  # noqa: E402 # isort:skip
gi.require_version('Gst', '1.0')  # noqa: E402 # isort:skip
gi.require_version('Gtk', '3.0')  # noqa: E402 # isort:skip
gi.require_version('GstVideo', '1.0')  # noqa: E402 # isort:skip
gi.require_version('GdkX11', '3.0')  # noqa: E402 # isort:skip
from gi.repository import Gst, Gtk  # noqa: E402 # isort:skip

from picast.settings import Settings


class VlcPlayer():

    def __init__(self, logger='picast'):
        self.logger = getLogger(logger)
        self.vlc = None

    def start(self):
        self.logger.debug("Start vlc client.")
        self.vlc = subprocess.Popen(["vlc", '--fullscreen', 'rtp://0.0.0.0:1028/wfd1.0/streamid=0'])

    def stop(self):
        if self.vlc is not None:
            self.logger.debug("Stop vlc client.")
            self.vlc.terminate()


class GstPlayer():
    def __init__(self, logger='picast'):
        self.config = Settings()
        self.logger = getLogger(logger)
        Gst.init(None)

    def on_message(self, bus, message):
        pass

    def start(self):
        gstcommand = "udpsrc port={0:d} caps=\"application/x-rtp, media=video\" ".format(self.config.rtp_port)
        gstcommand += "! rtph264depay ! omxh264dec ! videoconvert ! autovideosink"
        self.pipeline = Gst.parse_launch(gstcommand)
        self.logger.debug("Parse gst pipeline.")
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.on_eos)
        self.bus.connect('message::error', self.on_error)

        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)
        self.bus.connect('message', self.on_message)
        self.logger.debug("Start gst player...")
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.logger.debug("Stop gst player...")
        self.pipeline.set_state(Gst.State.NULL)

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            if hasattr(self, 'xid'):
                msg.src.set_window_handle(self.xid)

    def on_eos(self, bus, msg):
        self.logger.debug('on_eos(): seeking to start of video')
        self.pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            0
        )

    def on_error(self, bus, msg):
        self.logger.debug('on_error():{}'.format(msg.parse_error()))
