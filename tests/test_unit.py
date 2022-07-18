
from picast.video import RasberryPiVideo
from picast.wifip2p import WifiP2PServer
from picast.wpacli import WpaCli
from picast.exceptions import WpaException

import pytest


def _get_display_resolutions_mock(obj):
    obj.cea = 0x0101C3
    obj.vesa = 0x0208006
    obj.hh = 0x00


@pytest.mark.unit
def test_get_video_parameter(monkeypatch):
    def mockreturn(self):
        return _get_display_resolutions_mock(self)

    monkeypatch.setattr(RasberryPiVideo, "_get_display_resolutions", mockreturn)

    expected = "06 00 01 10 000101C3 00208006 00000000 00 0000 0000 00 none none"
    wvp = RasberryPiVideo()
    assert wvp.get_wfd_video_formats() == expected


@pytest.mark.unit
def test_wpacli_start_p2p_find(monkeypatch):

    def mockreturn(self, *args):
        assert args == ('p2p_find', 'type=progressive',)
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.start_p2p_find()


@pytest.mark.unit
def test_wpacli_start_p2p_find_negative(monkeypatch):

    def mockreturn(self, *args):
        assert args == ('p2p_find', 'type=progressive',)
        return "FAILED"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    with pytest.raises(WpaException):
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
def test_wpacli_stop_p2p_find_negative(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ('p2p_stop_find',)
        return "FAILED"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    with pytest.raises(WpaException):
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
def test_wpacli_set_device_name_negative(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("set", "device_name", "foo",)
        return "FAILED"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    with pytest.raises(WpaException):
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
def test_wpacli_set_device_type_negative(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("set", "device_type", "foo",)
        return "FAILED"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    with pytest.raises(WpaException):
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
def test_wpacli_set_p2p_go_ht40_negative(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("set", "p2p_go_ht40", "1",)
        return "FAILED"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    with pytest.raises(WpaException):
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
def test_wpacli_wfd_subelem_set_negative(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("wfd_subelem_set", "0", '00000000')
        return "FAILED"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    with pytest.raises(WpaException):
        wpacli.wfd_subelem_set(0, "00000000")


@pytest.mark.unit
def test_wpacli_p2p_group_add(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("p2p_group_add", 'persistent=42')
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.p2p_group_add("42")


@pytest.mark.unit
def test_wpacli_get_persistent_group_network_id(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ("list_networks", )
        return ["Selected interface 'p2p-dev-wlan0",
                "network id / ssid / bssid / flags",
                "0       Some_wifi any",
                "1       DIRECT-3E_picast       aa:22:cc:33:dd:44       [DISABLED][P2P-PERSISTENT]"]

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    assert wpacli.get_persistent_group_network_id("picast") == "1"

@pytest.mark.unit
def test_wpacli_wps_pin(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ('-i', 'w1p0', 'wps_pin', 'any', '12345678', '300')
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.set_wps_pin("w1p0", '12345678', 300)


@pytest.mark.unit
def test_wpacli_wps_pbc(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ('-i', 'w1p0', 'wps_pbc')
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.start_wps_pbc("w1p0")


@pytest.mark.unit
def test_wpacli_p2p_connect(monkeypatch):

    def mockreturn(self, *arg):
        assert arg == ('-i', 'w1p0', 'p2p_connect', 'peer01', '12345678')
        return "OK"

    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    wpacli.p2p_connect("w1p0", '12345678', 'peer01')


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
def test_wpa_check_p2p_interface_negative(monkeypatch):
    def mockreturn(self, *arg):
        assert arg == ('interface',)
        return ["Selected interface 'wlan0'", "Available interfaces:", "wlan0"]
    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    assert wpacli.check_p2p_interface() == False


@pytest.mark.unit
def test_wpa_check_p2p_interface_negative_dev(monkeypatch):
    def mockreturn(self, *arg):
        assert arg == ('interface',)
        return ["Selected interface 'p2p-dev-wlan0'", "Available interfaces:", "p2p-dev-wlan0", "wlan0"]
    monkeypatch.setattr(WpaCli, "cmd", mockreturn)
    wpacli = WpaCli()
    assert wpacli.check_p2p_interface() == False


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

