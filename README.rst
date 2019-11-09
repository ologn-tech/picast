A Simple Wireless Display Receiver on Raspberry Pi
==================================================

.. image:: https://travis-ci.org/miurahr/picast.svg?branch=master
    :target: https://travis-ci.org/miurahr/picast
    :alt: Travis test status

.. image:: https://badge.fury.io/py/picast.svg
    :target: https://badge.fury.io/py/picast

.. image:: https://readthedocs.org/projects/picast/badge/?version=latest
    :target: https://picast.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation status

.. image:: https://coveralls.io/repos/github/miurahr/picast/badge.svg?branch=master
    :target: https://coveralls.io/github/miurahr/picast?branch=master


Description
-----------

picast is a simple wifi display receiver written by Python3 on Raspberry Pi.


Dependency
----------

picast depends several external utilities and some are only on Raspbian.

- tvservice  (raspbian only)
- udhcpd (debian/ubuntu only)
- wpa_supplicant
- wpa_cli
- vlc


Installation
------------

Run apt install command on Raspbian(buster or later) / Raspberry Pi Zero W/WH, RaPi 3B+, RaPi 4.

.. code-block:: console

    $ sudo apt install net-tools python3 udhcpd python-gst-1.0 libgtk-3-dev python3-gi gir1.2-gtk-3.0
    $ sudo apt install gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0
    $ sudo apt install gstreamer1.0-plugins-good gstreamer1.0-gtk3 gstreamer1.0-plugins-rtp
    $ sudo apt install gstreamer1.0-omx-rpi gstreamer1.0-omx-rpi-config vlc
    $ sudo apt install --no-install-recommends lxde

For debug and development;

.. code-block:: console

    $ sudo apt install gstreamer1.0-tools

.. code-block:: console

    $ git clone https://github.com/miurahr/picast.git picast


Run
---

.. code-block:: console

    $ cd picast
    $ bin/picast


Preparation
-----------

Increase GPU memory for decoding fullHD video stream.
add `gpu_mem=128`  to `/boot/config.txt`


Usage
-----

Picast search for the wireless display named "picast" on the source device you want to cast.
Use "12345678" for a WPS PIN number.
It is recommended to initiate the termination of the receiver on the source side.
After Pi connects to the source, it has an IP address of ``192.168.173.80``.

These parameters are configured in `settings.ini`.


Autostart
---------

Edit `/home/pi/.config/lxsessions/LXDE/autostart`

.. code-block:: bash

    @xscreensaver -no-splash
    @lxterminal -l -e /home/pi/picast/bin/picast


Debug
-----

There is a debug log at `/var/tmp/picast.log`. It is configured in `logging.ini`.


Known issues
------------

* Latency: Limited by the implementation of the RTP player used.

* WiFi: The on-board WiFi chip on Pi 3/Zero W only supports 2.4GHz. Due to the overcrowded nature of the 2.4GHz
  spectrum and the use of unreliable rtp transmission, you may experience some video glitching/audio stuttering.
  It may be better with Pi 3B+/4 that support IEEE802.11ac 5GHz.

* HDCP(content protection): Neither the key nor the hardware is available on Pi and therefore is not supported.


License and copyright
---------------------

* Copyright 2019 Hiroshi Miura
* Copyright 2018 Hsun-Wei Cho

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
