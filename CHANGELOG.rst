=========
changeLog
=========

All notable changes to this project will be documented in this file.

`Unreleased`_
=============

Added
-----

Changed
-------

Fixed
-----

Deprecated
----------

Removed
-------

Security
--------

`v0.3.2`_
=========

Fixed
-----

* Fix ip address error for zeroconf constructor(#9).


`v0.3.1`_
=========

Fixed
-----

* Fix settings.ini not found error on distribution.


`v0.3`_
=======

Changed
-------

* Release artifacts with github actions.
* Use setuptools_scm to automate version.
* Packaging metadata in setup.cfg
* Auto generate binary by build backend.

Fixed
-----

* Several document errors.

`v0.2.4`_
=========

Added
-----

* Comments for parameter configs.
* Parameters Microsoft V2 extensions.


`v0.2.3`_
=========

Changed
-------

* Change class name RtspSink to RTSPSink

Fixed
-----

* Watching socket timeout and break connection.


v0.2.2
======

Changed
-------

* Update README to use pypi.org for distribution.
* Refactoring RTSPSink class

Fixed
-----

* Fix config loading error.

`v0.2.1`_
=========

Added
-----

* Introduce [p2p] wps_mode= in settings.ini.
  can be 'pbc' ie. Push the Button, or 'pin'

* Add documentation for settings.

Changed
-------

* Add p2p_connect() and start_wps_pbc() methods.
* Improve CLI staff.

Fixed
-----

* main() drop unused asyncio staff.

`v0.2`_
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


`v0.1`_
=======

* First working release.

`v0.0.1`_
=========

* Forked from lazycast.


.. _Unreleased: https://github.com/miurahr/picast/compare/v0.3.2...HEAD
.. _v0.3.2: https://github.com/miurahr/picast/compare/v0.3.1...v0.3.2
.. _v0.3.1: https://github.com/miurahr/picast/compare/v0.3...v0.3.1
.. _v0.3: https://github.com/miurahr/picast/compare/v0.2.4...v0.3
.. _v0.2.4: https://github.com/miurahr/picast/compare/v0.2.3...v0.2.4
.. _v0.2.3: https://github.com/miurahr/picast/compare/v0.2.1...v0.2.3
.. _v0.2.1: https://github.com/miurahr/picast/compare/v0.2...v0.2.1
.. _v0.2: https://github.com/miurahr/picast/compare/v0.1...v0.2
.. _v0.1: https://github.com/miurahr/picast/compare/v0.0.1...v0.1
.. _v0.0.1: https://github.com/miurahr/picast/compare/lazycast...v0.0.1
