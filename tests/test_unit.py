
from picast.rtspserver import RtspServer
from picast.video import WfdVideoParameters
from picast.wifip2p import WifiP2PServer
from picast.wpacli import WpaCli

import pytest


@pytest.mark.unit
def test_get_video_parameter(monkeypatch):
    def mockreturn(self):
        return 0x0141, 0x08288a0a, 0x0

    monkeypatch.setattr(WfdVideoParameters, "get_display_resolutions", mockreturn)

    expected = "06 00 02 02 00000141 08288A0A 00000000 00 0000 0000 00 none none"
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
def test_wpacli_wfd_subelem_set(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("wfd_subelem_set", "0", '00000000')
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.wfd_subelem_set(0, "00000000")


@pytest.mark.unit
def test_wpacli_p2p_group_add(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("p2p_group_add", 'group')
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.p2p_group_add("group")


@pytest.mark.unit
def test_wpacli_wps_pin(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ('-i', 'w1p0', 'wps_pin', 'any', '12345678', '300')
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.set_wps_pin("w1p0", '12345678', 300)


@pytest.mark.unit
def test_wpa_p2p_interface(monkeypatch):
    def mockreturn(self, *arg):
        assert arg == ('interface',)
        return ["Selected interface 'p2p-wlp4s0'", "Available interfaces:", "p2p-wlp4s0", "wlp4s0"]
    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    result = wpacli.get_p2p_interface()
    assert result == "p2p-wlp4s0"


@pytest.mark.unit
def test_wpa_check_p2p_interface(monkeypatch):
    def mockreturn(self, *arg):
        assert arg == ('interface',)
        return ["Selected interface 'p2p-wlp4s0'", "Available interfaces:", "p2p-wlp4s0", "wlp4s0"]
    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    assert wpacli.check_p2p_interface()


@pytest.mark.unit
def test_wpa_get_interface(monkeypatch):
    def mockreturn(self, *arg):
        assert arg == ('interface',)
        return ["Selected interface 'p2p-wlp4s0'", "Available interfaces:", "p2p-wlp4s0", "wlp4s0"]
    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    selected, interfaces = wpacli.get_interfaces()
    assert selected == 'p2p-wlp4s0'
    assert interfaces == ['p2p-wlp4s0', 'wlp4s0']


@pytest.mark.unit
def test_devinfo(monkeypatch):
    def mockreturn(self, *arg):
        return
    monkeypatch.setattr(WifiP2PServer, "set_p2p_interface", mockreturn)
    p2p = WifiP2PServer()
    assert  p2p.wfd_devinfo() == '00060151022a012c'


@pytest.mark.unit
def test_devinfo2(monkeypatch):
    def mockreturn(self, *arg):
        return
    monkeypatch.setattr(WifiP2PServer, "set_p2p_interface", mockreturn)
    p2p = WifiP2PServer()
    assert p2p.wfd_devinfo2() == '00020001'


@pytest.mark.unit
def test_ext_cap(monkeypatch):
    def mockreturn(self, *arg):
        return
    monkeypatch.setattr(WifiP2PServer, "set_p2p_interface", mockreturn)
    p2p = WifiP2PServer()
    assert p2p.wfd_ext_cap(uibc=False, i2c=False) == '00020000'
    assert p2p.wfd_ext_cap(uibc=True, i2c=False) == '00020001'
    assert p2p.wfd_ext_cap(uibc=False, i2c=True) == '00020002'


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

