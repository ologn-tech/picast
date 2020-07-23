---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**Related issue**
(if exist)

**Settings**
* command line you launch.
* Attach your settings, if run with default settings, upload picast/settings.ini file.
* Attach your logging settings, if running with default configuration, upload picast/logging.ini

**Error Message**
* Message on console.
* Attach a log file, when default configuration, upload /var/tmp/picast.log
 
**picast server environments (please complete the following information):**
 - Raspberry Pi model: [e.g. RaspberryPi Zero W]
 - OS: [e.g. raspbian buster Lite]
 - Python version: [e.g. 3.6.9]
 - Python libraries (pip list):
   * pygobject: [e.g. 3.26.1]
   * zeroconf: [e.g. 0.23.0]
   * ifaddr: [e.g. 0.1.6]
 - External libraries and utilities(apt show):
   * Gtk: [e.g. 3.22.30]
   * vlc: [e.g. 3.0.8]
   * wpasupplicant: [e.g.2:2.9-1]
   * udhcpd:
   * tvservice:
 - Monitor model and resolutions:
   * vendor/model: [e.g. ASUS 13' portable monitor with full-HD]
   * display configuration: `tvservice --status` command output.
 - Running processes:
   * output of `ps ax` command. 

**Client environments**
 - Device type: [e.g. Google nexus 5, Dell note PC]
 - Client OS: [e.g. Android 10, Windows 1903, Mint linux 17.3]
 
**Additional context**
Add any other context about the problem here.
