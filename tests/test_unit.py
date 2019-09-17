from picast.video import WfdVideoParameters, Res
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
    assert  p2p.wfd_devinfo() == '00060151022a012c'


@pytest.mark.unit
def test_get_resolutions(monkeypatch):
    def mockreturn(self):
        return b'1920x1080     60.05\n1680x1050     59.95\n1600x1024     60.17\n1400x1050     59.98\n1600x900      59.99\n1280x1024     60.02\n1440x900      59.89\n1400x900      59.96\n1280x960      60.00\n1440x810      60.00\n1368x768      59.88\n1360x768      59.80\n1280x800      59.99\n1152x864      60.00\n1280x720      60.00\n1024x768      60.04\n800x600       60.00\n640x480       60.00\n640x400       59.88\n'  # noqa

    monkeypatch.setattr(WfdVideoParameters, "retrieve_xrandr", mockreturn)
    vpara = WfdVideoParameters()
    cea = [
        Res(8, 1920, 1080, 60),
        Res(6, 1280, 720, 60),
        Res(0, 640, 480, 60),
    ]
    vesa = [
        Res(27, 1680, 1050, 60),
        Res(21, 1600, 900, 60),
        Res(15, 1280, 1024, 60),
        Res(19, 1440, 900, 60),
        Res(11, 1360, 768, 60),
        Res(9, 1280, 800, 60),
        Res(3, 1024, 768, 60),
        Res(1, 800, 600, 60),
    ]
    expected = (cea, vesa)
    assert vpara.get_display_resolutions() == expected
