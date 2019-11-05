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

`v0.2'_
=======

Added
-----

* Test for python 3.7 and 3.8
  - Install PyObject through pip.
* Test typing with mypy.
  - dependency for gst-python-stubs and PyObject-stubs

Changed
-------

* Use AsyncIO for network communication.(#4)
* Handle header parameters as str.

Fixed
-----

* Bug: fails to recieve M4 message because M3 reciever can read both M3 and M4.


`v0.1'_
=======

* First working release.

.. _Unreleased: https://github.com/miurahr/picast/compare/v0.1...HEAD
.. _v0.2: https://github.com/miurahr/picast/releases/tag/v0.1...v0.2
.. _v0.1: https://github.com/miurahr/picast/releases/tag/v0.0.1...v0.1
