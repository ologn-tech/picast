import configparser
import os

from picast.settings import Settings
from picast.video import WfdVideoParameters
from picast.wifip2p import WifiP2PServer
from picast.wpacli import WpaCli

import pytest


@pytest.mark.unit
def test_config_read():
    assert Settings().logger == 'picast'


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
