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
from gi.repository import Gst  # noqa: E402 # isort:skip

from .settings import Settings  # noqa: E402 # isort:skip


class NopPlayer():

    def __init__(self, logger='picast'):
        self.logger = getLogger(logger)
        self.proc = None

    def start(self):
        self.logger.debug("Start nop client.")
        self.proc = subprocess.Popen(["echo", 'rtp://0.0.0.0:1028/wfd1.0/streamid=0'])

    def stop(self):
        if self.proc is not None:
            self.logger.debug("Stop nop client.")
            self.proc.terminate()


class VlcPlayer():

    def __init__(self, logger='picast'):
        self.config = Settings()
        self.logger = getLogger(logger)
        self.vlc = None

    def start(self):
        self.logger.debug("Start vlc client.")
        self.vlc = subprocess.Popen(["cvlc", '--fullscreen', '--file-logging', '--logfile', self.config.player_log_file, 'rtp://0.0.0.0:1028/wfd1.0/streamid=0'])

    def stop(self):
        if self.vlc is not None:
            self.logger.debug("Stop vlc client.")
            self.vlc.terminate()


class GstPlayer():
    def __init__(self, logger='picast'):
        self.config = Settings()
        self.logger = getLogger(logger)
        Gst.init(None)

    def start(self):
        self.pipeline = Gst.Pipeline()

        src = Gst.ElementFactory.make('udpsrc')
        src.set_property('port', self.config.rtp_port)
        src.set_property('caps', "application/x-rtp, media=video")

        h264 = Gst.ElementFactory.make('rtph264depay')
        omxdecode = Gst.ElementFactory.make(self.config.gst_decoder)
        vconv = Gst.ElementFactory.make('videoconvert')
        sink = Gst.ElementFactory.make('autovideosink')

        for ele in [src, h264, omxdecode, vconv, sink]:
            self.pipeline.add(ele)

        src.link(h264)
        h264.link(omxdecode)
        omxdecode.link(vconv)
        vconv.link(sink)

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message)
        self.logger.debug("Start gst player...")
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.logger.debug("Stop gst player...")
        self.pipeline.set_state(Gst.State.NULL)

    def on_message(self, bus, message):
        mtype = message.type
        if mtype == Gst.MessageType.EOS:
            self.pipeline.seek_simple(
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                0
            )
        elif mtype == Gst.MessageType.ERROR:
            if message.get_structure().get_name() == 'prepare-window-handle':
                if hasattr(self, 'xid'):
                    message.src.set_window_handle(self.xid)
        elif mtype == Gst.MessageType.WARNING:
            self.logger.debug('on_error():{}'.format(message.parse_error()))

        return True
