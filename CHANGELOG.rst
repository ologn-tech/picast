=========
changeLog
=========

All notable changes to this project will be documented in this file.

***************
Current changes
***************

`Unreleased`_
=============

Added
-----

* Introduce [p2p] wps_mode= in settings.ini.
  can be 'pbc' ie. Push the Button, or 'pin'

* Add documentation for settings.

Changed
-------

* Add p2p_connect() and start_wps_pbc() methods.

Fixed
-----

* main() drop unused asyncio staff.

Deprecated
----------

Removed
-------

Security
--------

`v0.2'_
=======

Added
-----

* Test for python 3.7 and 3.8
  - Install PyObject through pip.
  - Add network protocol functional tests.
* Test typing with mypy.
  - dependency for gst-python-stubs and PyObject-stubs

Changed
-------

* Introduce RTSPTransport class to handle network connection.

Fixed
-----

* Bug: fails to recieve M4 message because M3 reciever can read both M3 and M4.


`v0.1'_
=======

* First working release.

.. _Unreleased: https://github.com/miurahr/picast/compare/v0.1...HEAD
.. _v0.2: https://github.com/miurahr/picast/releases/tag/v0.1...v0.2
.. _v0.1: https://github.com/miurahr/picast/releases/tag/v0.0.1...v0.1
