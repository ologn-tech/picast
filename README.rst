pycast: A Simple Wireless Display Receiver
==========================================

Description
-----------

pycast is a simple wifi display receiver written by Python.


Installation
------------

.. code-block::
    $ sudo apt install net-tools python3 udhcpd omxplayer vlc
    $ sudo apt install --no-install-recommends lxde pulseaudio

Note: udhcpd is a DHCP server for Ubuntu and Debian.


Usage
-----

.. code-block::
    $ python3 pycast.py

Then, search for the wireless display named "pycast" on the source device you want to cast.
Use "12345678" for a WPS PIN number.
It is recommended to initiate the termination of the receiver on the source side.

After Pi connects to the source, it has an IP address of ``192.168.173.1``
and this connection can be reused for other purposes like SSH.

Known issues
------------

* Resolution: pycast advertised all resolutions rather than connected display resolution.

* Latency: Limited by the implementation of the rtp player used.

* WiFi: The on-board WiFi chip on Pi 3/Zero W only supports 2.4GHz. Due to the overcrowded nature of the 2.4GHz
  spectrum and the use of unreliable rtp transmission, you may experience some video glitching/audio stuttering.

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
