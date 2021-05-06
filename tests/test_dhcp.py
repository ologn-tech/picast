import os
import subprocess
import tempfile

import pytest

from picast.dhcpd import Dhcpd

class ProcessMock:

    def __init__(self, args, stdout, stderr, returncode=0, timeout=False):
        self.returncode = returncode
        self.timeout = timeout
        self.terminate_count = 0
        assert args[0] == 'sudo'
        assert args[1] == 'udhcpd'

    def communicate(self, timeout):
        if self.timeout:
            raise subprocess.TimeoutExpired(cmd="test cmd", timeout=42)
        return ('stdout', 'stderr')

    def terminate(self):
        self.terminate_count += 1

@pytest.mark.unit
def test_dhcpd_start_stop(monkeypatch):
    def mock_proc(args, stdout, stderr):
        return ProcessMock(args, stdout, stderr)

    def mock_os_system(args):
        pass

    monkeypatch.setattr(subprocess, 'Popen', mock_proc)
    monkeypatch.setattr(os, 'system', mock_os_system)

    dhcpd = Dhcpd('p2p-wlan0-0')
    dhcpd.start()
    dhcpd.stop()
    assert dhcpd.dhcpd.terminate_count == 1

@pytest.mark.unit
def test_dhcpd_start_failed(monkeypatch):
    def mock_proc(args, stdout, stderr):
        return ProcessMock(args, stdout, stderr, 1)

    def mock_os_exit(args):
        pass

    monkeypatch.setattr(subprocess, 'Popen', mock_proc)
    monkeypatch.setattr(os, '_exit', mock_os_exit)

    dhcpd = Dhcpd('p2p-wlan0-0')
    dhcpd.start()

@pytest.mark.unit
def test_dhcpd_start_with_timeout(monkeypatch):
    def mock_proc(args, stdout, stderr):
        return ProcessMock(args, stdout, stderr, 0, True)

    monkeypatch.setattr(subprocess, 'Popen', mock_proc)

    dhcpd = Dhcpd('p2p-wlan0-0')
    dhcpd.start()

