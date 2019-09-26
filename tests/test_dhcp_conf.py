
import pytest

from picast.dhcpd import Dhcpd


@pytest.mark.unit
def test_dhcpd_conf():
    dhcpd = Dhcpd('p2p-wlan0-0')
    with open(dhcpd.conf_path, 'r') as c:
        conf = c.readlines()
    assert conf == ["start  192.168.173.80\n", "end 192.168.173.80\n",
                    "interface p2p-wlan0-0\n", "notify_file dumpleases\n",
                    "option subnet 255.255.255.0\n", "option lease 300\n"]
