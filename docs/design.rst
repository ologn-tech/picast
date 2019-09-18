:tocdepth: 2

.. _design:

Design
======

`picast` project try to provide miracast display sink/reciever functionarity on Raspberry Pi Zero W.
There is no certification from WiFi Alliance, and it is built upon try-and-error basis with
existent devices, there is no gurantee to compliance to WiFi alliance specifications.


Modules
=======

`picast` consist with several modules.

- `picast.dhcpd` provide dhcp server function by running external `udhcpd` daemon with custom configuration.

- `picast.discovery` provide an interface to mDNS/SD network to register and query display sink and source.

- `picast.player` provide a RTP movie and audio player, supporting H.264 and AC3/AAC/LPCM audio codecs.

- `picast.settings` is a place to configure an application.

- `picast.video` checks platform and provide proper wfd-video-formats parameter for miracast negotiation.

- `picast.wifip2p` setup `wpa_supplicant` to accept connection from miracast source.

- `picast.wpacli` provide methods to configure `wpa_supplicant` through `wpa-cli` command line.

- `picast.picast` is a core module to define controller and communicator with miracast source throught RTSP.


GStreamer
=========

`picast` depends upon `GStreamer` video/audio handling framework and its python bindings.
`picast` uses 'OpenMAX' codec API to decode H.264 video container.


Threads
=======

`picast` uses threading technic to realize a controller communication through RTSP and RTP player control


Tests
=====

There are several unittests for functions but it is not enough and there is possibility to exist defeat.


Logging
=======

`picast` defines module level logger and output many debug messages.

