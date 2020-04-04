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

import argparse
import os
from logging import config as LoggingConfig
from logging import getLogger
from typing import Any, Optional, Union

import gi

os.putenv('DISPLAY', ':0')  # noqa: E402 # isort:skip
gi.require_version('Gst', '1.0')  # noqa: E402 # isort:skip
gi.require_version('Gtk', '3.0')  # noqa: E402 # isort:skip
gi.require_version('GstVideo', '1.0')  # noqa: E402 # isort:skip
gi.require_version('GdkX11', '3.0')  # noqa: E402 # isort:skip

from picast.rtspsink import RtspSink  # noqa: E402 # isort:skip
from picast.player import GstPlayer, VlcPlayer  # noqa: E402 # isort:skip
from picast.settings import Settings  # noqa: E402 # isort:skip
from picast.wifip2p import WifiP2PServer  # noqa: E402 # isort:skip


def main(arg: Optional[Any] = None):
    parser = argparse.ArgumentParser(prog='picast', description='picast',
                                     formatter_class=argparse.RawTextHelpFormatter, add_help=True)
    parser.add_argument("--debug", action="store_true", help="Verbose debug output")
    parser.add_argument("-c", "--config", help="Specify configuration file.")

    args = parser.parse_args(arg)
    if args.config:
        config_file = args.config
        if os.path.exists(config_file) and os.path.isfile(config_file):
            pass
        else:
            config_file = None
    else:
        config_file = None

    # ------------------- start of configurations
    # it should call first: load configurations from ini files
    config = Settings(config=config_file)
    package_dir = os.path.join(os.path.dirname(__file__))
    if config.logging_config:
        logging_ini = config.logging_config
        if not os.path.exists(logging_ini):
            if os.path.exists(os.path.join(package_dir, logging_ini)):
                logging_ini = os.path.join(package_dir, logging_ini)
    else:
        logging_ini = os.path.join(package_dir, "logging.ini")
    LoggingConfig.fileConfig(logging_ini)
    logger = getLogger(config.logger)
    if args.debug:
        logger.setLevel("DEBUG")

    if config.player == "gst":
        player = GstPlayer()  # type: Optional[Union[GstPlayer, VlcPlayer]]
    elif config.player == "vlc":
        player = VlcPlayer()
    else:
        player = None
        logger.fatal("FATAL: Unknown player name option!: {}".format(config.player))
        exit(1)
    # ------------------- end of configurations

    wifip2p = WifiP2PServer()
    rtspsink = RtspSink(player)

    wifip2p.start()
    rtspsink.start()

    rtspsink.join()
    wifip2p.join()


if __name__ == "__main__":
    main()
