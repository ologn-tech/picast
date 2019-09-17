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
import sys
from logging import getLogger, DEBUG, StreamHandler

import gi

os.putenv('DISPLAY', ':0')  # noqa: E402 # isort:skip
gi.require_version('Gst', '1.0')  # noqa: E402 # isort:skip
gi.require_version('Gtk', '3.0')  # noqa: E402 # isort:skip
gi.require_version('GstVideo', '1.0')  # noqa: E402 # isort:skip
gi.require_version('GdkX11', '3.0')  # noqa: E402 # isort:skip
from gi.repository import Gtk  # noqa: E402 # isort:skip

from .wifip2p import WifiP2PServer
from .picast import PiCast
from .player import GstPlayer


def main():
    logger = getLogger("PiCast")
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)
    logger.propagate = True

    wifip2p = WifiP2PServer()
    wifip2p.start()

    window = Gtk.Window()
    window.set_name('PiCast')
    window.connect('destroy', Gtk.main_quit)
    window.show_all()

    player = GstPlayer()
    picast = PiCast(window, player)

    picast.start()

    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
