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
import logging
import os


class Settings:
    wp_device_name = 'picast'
    wp_device_type = "7-0050F204-1"
    wp_group_name = 'persistent'
    pin = '12345678'
    timeout = 300
    rtsp_port = 7236
    rtp_port = 1028
    myaddress = '192.168.173.1'
    peeraddress = '192.168.173.80'
    netmask = '255.255.255.0'
    logger = 'picast'
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(thread)d %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console':{
                'level':'DEBUG',
                'class':'logging.StreamHandler',
                'formatter': 'simple'
            },
            'file':{
                'level':'DEBUG',
                'class':'picast.settings.PicastFileHandler',
            }
        },
        'loggers': {
            'picast': {
                'handlers':['console', 'file'],
                'propagate': True,
                'level':'DEBUG',
            },
            'root': {
                'handlers': ['console'],
                'level': 'DEBUG'
            },
        }

    }


class PicastFileHandler(logging.FileHandler):

    def __init__(self):
        path = '/var/log/picast'
        fileName = 'picast.log'
        mode = 'a'
        super(PicastFileHandler, self).__init__(os.path.join(path, fileName), mode)