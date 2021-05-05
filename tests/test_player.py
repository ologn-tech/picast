import os
import subprocess
import tempfile

import pytest

from picast.players.nop import NopPlayer
from picast.players.vlc import VlcPlayer

class ProcessMock:

    def __init__(self, args, expect_arg):
        self.terminate_count = 0
        assert args[0] == expect_arg

    def terminate(self):
        self.terminate_count += 1

@pytest.mark.unit
def test_nop_player_start_stop(monkeypatch):
    def mock_proc(args):
        return ProcessMock(args, 'echo')

    monkeypatch.setattr(subprocess, 'Popen', mock_proc)

    player = NopPlayer()
    player.start()
    player.stop()
    assert player.proc.terminate_count == 1

@pytest.mark.unit
def test_vlc_player_start_stop(monkeypatch):
    def mock_proc(args):
        return ProcessMock(args, 'cvlc')

    monkeypatch.setattr(subprocess, 'Popen', mock_proc)

    player = VlcPlayer()
    player.start()
    player.stop()
    assert player.vlc.terminate_count == 1
