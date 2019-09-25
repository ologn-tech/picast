import os
from logging import config as LoggingConfig

from picast.video import WfdVideoParameters
from picast.wifip2p import WifiP2PServer
from picast.wpacli import WpaCli

import pytest


@pytest.mark.unit
def test_get_video_parameter(monkeypatch):
    def mockreturn(self):
        return 0x0141, 0x08288a0a, 0x0

    monkeypatch.setattr(WfdVideoParameters, "get_display_resolutions", mockreturn)

    expected = "wfd_audio_codecs: AAC 00000001 00, LPCM 00000002 00\r\n" \
               "wfd_video_formats: 06 00 03 02 00000141 08288A0A 00000000 00 0000 0000 00 none none\r\n" \
               "wfd_3d_video_formats: none\r\nwfd_coupled_sink: none\r\nwfd_display_edid: none\r\n" \
               "wfd_connector_type: 05\r\nwfd_uibc_capability: none\r\nwfd_standby_resume_capability: none\r\n" \
               "wfd_content_protection: none\r\n"
    wvp = WfdVideoParameters()
    assert wvp.get_video_parameter() == expected


@pytest.mark.unit
def test_wpacli_start_p2p_find(monkeypatch):

    def mockreturn(self, *args):
        assert args == ('p2p_find', 'type=progressive',)
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.start_p2p_find()


@pytest.mark.unit
def test_wpacli_stop_p2p_find(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ('p2p_stop_find',)
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.stop_p2p_find()


@pytest.mark.unit
def test_wpacli_set_device_name(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("set", "device_name", "foo",)
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.set_device_name("foo")


@pytest.mark.unit
def test_wpacli_set_device_type(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("set", "device_type", "foo",)
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.set_device_type("foo")


@pytest.mark.unit
def test_wpacli_set_p2p_go_ht40(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("set", "p2p_go_ht40", "1",)
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.set_p2p_go_ht40()


@pytest.mark.unit
def test_devinfo(monkeypatch):
    def mockreturn(self, *arg):
        return
    monkeypatch.setattr(WifiP2PServer, "set_p2p_interface", mockreturn)
    p2p = WifiP2PServer()
    assert  p2p.wfd_devinfo() == '00060151022a012c'


def _tvservice_mock(cmd):
    """Return actual modes retrieved from Raspberry Pi Zero WH with FHD monitor."""
    if cmd == "tvservice -m CEA -j":
        return '[{ "code":1, "width":640, "height":480, "rate":60, "aspect_ratio":"4:3", "scan":"p", "3d_modes":[] },' \
               ' { "code":2, "width":720, "height":480, "rate":60, "aspect_ratio":"4:3", "scan":"p", "3d_modes":[] },' \
               ' { "code":3, "width":720, "height":480, "rate":60, "aspect_ratio":"16:9", "scan":"p", "3d_modes":[] },' \
               ' { "code":4, "width":1280, "height":720, "rate":60, "aspect_ratio":"16:9", "scan":"p", "3d_modes":[] },' \
               ' { "code":16, "width":1920, "height":1080, "rate":60, "aspect_ratio":"16:9", "scan":"p", "3d_modes":[] }, ' \
               '{ "code":32, "width":1920, "height":1080, "rate":24, "aspect_ratio":"16:9", "scan":"p", "3d_modes":[] }, ' \
               '{ "code":34, "width":1920, "height":1080, "rate":30, "aspect_ratio":"16:9", "scan":"p", "3d_modes":[] } ]'
    elif cmd == "tvservice -m DMT -j":
        return '[{ "code":4, "width":640, "height":480, "rate":60, "aspect_ratio":"4:3", "scan":"p", "3d_modes":[] },' \
               ' { "code":9, "width":800, "height":600, "rate":60, "aspect_ratio":"4:3", "scan":"p", "3d_modes":[] },' \
               ' { "code":16, "width":1024, "height":768, "rate":60, "aspect_ratio":"4:3", "scan":"p", "3d_modes":[] },' \
               ' { "code":35, "width":1280, "height":1024, "rate":60, "aspect_ratio":"5:4", "scan":"p", "3d_modes":[] },' \
               ' { "code":83, "width":1600, "height":900, "rate":60, "aspect_ratio":"16:9", "scan":"p", "3d_modes":[] },' \
               ' { "code":85, "width":1280, "height":720, "rate":60, "aspect_ratio":"16:9", "scan":"p", "3d_modes":[] }]'
    else:
        return None

@pytest.mark.unit
def test_tvservice_cea(monkeypatch):
    def mockreturn(self, cmd):
        return _tvservice_mock(cmd)
    monkeypatch.setattr(WfdVideoParameters, "_call_tvservice", mockreturn)
    v = WfdVideoParameters()
    param = v.retrieve_tvservice(WfdVideoParameters.TvModes.CEA)
    assert param[0]["code"] == 1
    assert param[1]["width"] == 720


@pytest.mark.unit
def test_tvservice_dmt(monkeypatch):
    def mockreturn(self, cmd):
        return _tvservice_mock(cmd)
    monkeypatch.setattr(WfdVideoParameters, "_call_tvservice", mockreturn)
    v = WfdVideoParameters()
    param = v.retrieve_tvservice(WfdVideoParameters.TvModes.DMT)
    assert param[0]["code"] == 4
    assert param[1]["width"] == 800


@pytest.mark.unit
def test_load_resolutons_json():
    v = WfdVideoParameters()
    assert v.resolutions['cea'] is not None
    assert v.resolutions['vesa'] is not None
    assert len(v.resolutions['cea']) == 12
    assert len(v.resolutions['vesa']) == 8


@pytest.mark.unit
def test_get_display_resolution(monkeypatch):
    def mockreturn(self, cmd):
        return _tvservice_mock(cmd)
    monkeypatch.setattr(WfdVideoParameters, "_call_tvservice", mockreturn)
    v = WfdVideoParameters()
    cea, vesa, hh = v.get_display_resolutions()
    assert cea == 0x0101C3
    assert vesa == 0x0208006
    assert hh == 0x00
