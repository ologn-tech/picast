:tocdepth: 2

.. _settings:

Settings
========

There are several configurations you can customize in `settings.ini`.

Section [logging]
-----------------

logger

    'logger' is a name of logging. You can change if you want.
    It is used for `logging.getLogger(<name>)` as a its `<name>`.

config

    'config' is a filename of logging configuration. It should be
    ini style configuration that syntax is described in `configuring logging`_
    section of python manual.

.. _configuring logging: https://docs.python.org/3.8/howto/logging.html#configuring-logging


Section [network]
-----------------

myaddress

    'myaddress' is an IPv4 address to attach WiFi-P2P wifi device.

peeraddress

    'peeraddress' is an IPv4 address to lease to source device by dhcp server.

netmask

    'netmask' is an IPv4 netmask when leasing address.

rtsp_port

    'rtsp_port' is a port to use for negotiation between sink and source.

rtp_port

    'rtp_port' is a port to use displaying source image onto sink monitor.


Section [p2p]
-------------

device_name

    'device_name' is used to display a name of receiver name on source device.

device_type

    'device_type' is used to specify a `WiFi-P2P device_type`.

group_name

    'group_name' is used to specify a `WiFi-P2P Group` name.

wps_mode

    'wps_mode' is used to specify which mode for WPS configuration.
    `pbc` is for 'Push the Button' and `pin` is for static PIN used.

pin

    'pin' for wps_mode=pin configuration.

timeout

    'timeout' for wps_mode=pin configuration.


Section [player]
----------------

name

    'name' of player, one of `vlc` or `gst` is accepted.


Section [gst]
-------------

decoder

    'decoder' is a gst plugin name to decode H.264/H.265 video.
    `omxh264dec` is recommended for Raspberry Pi video chip.
    It is used when player name is specified as `gst`.


Section [wfd_parameter]
-----------------------

wfd_audio_codecs

    It is used as a value for `wfd_audio_codecs` parameter when negotiation.
    default value is `AAC 00000001 00, LPCM 00000002 00`

wfd_connector_type

    It is used as a value for `wfd_connector_type` parameter when negotiation.
    HDMI is `05`.


.. _resolutions:

Resolutions data
================

There is a `resolutions.json` file that describe Raspberry Pi video resolutions data.
It is used to determine which video mode is supported in current RaPi device and monitor device.

Resolutions are retrived by `tvservice` command. `code` number is used to determine its output.
`mode` is a WiFi Direct video mode corresponding with specified resolution.

If you want to porting picast to another device, you should create a new json file and
update video.py module.
