from picast.video import WfdVideoParameters
from picast.wifip2p import WifiP2PServer
from picast.wpacli import WpaCli

import pytest


@pytest.mark.unit
def test_get_video_parameter():
    expected = "wfd_audio_codecs: AAC 00000001 00, LPCM 00000002 00\r\n" \
               "wfd_video_formats: 08 00 03 10 0001FFFF 0FFFFFFF 00000000 00 0000 0000 00 none none\r\n" \
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
def test_devinfo():
    p2p = WifiP2PServer()
    assert '00060151022a012c' == p2p.wfd_devinfo()
