import os
import tempfile
from logging import config as LoggingConfig

from picast.settings import Settings

import pytest


@pytest.mark.unit
def test_logging_config():
    LoggingConfig.fileConfig(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'picast', 'logging.ini'))


@pytest.mark.unit
def test_config_override():
    fd, temp_path = tempfile.mkstemp()
    with open(temp_path, "w") as f:
        f.write("[player]\n")
        f.write("name=nop\n")
    Settings()._config = None # Clean singletone state
    assert Settings().device_name == 'picast'
    assert Settings().player == 'vlc'
    Settings()._config = None # Clena singletone state
    assert Settings(config=temp_path).device_name == 'picast'
    assert Settings(config=temp_path).player == 'nop'
    Settings()._config = None # Clena singletone state
    os.unlink(temp_path)


@pytest.mark.unit
def test_config_logger():
    assert Settings().logger == 'picast'


@pytest.mark.unit
def test_config_logging_config():
    assert Settings().logging_config == 'logging.ini'


@pytest.mark.unit
def test_config_myaddress():
    assert Settings().myaddress == '192.168.173.1'


@pytest.mark.unit
def test_config_peeraddress():
    assert Settings().peeraddress == '192.168.173.80'


@pytest.mark.unit
def test_config_netmask():
    assert Settings().netmask == '255.255.255.0'


@pytest.mark.unit
def test_config_rtp_port():
    assert Settings().rtp_port == 1028


@pytest.mark.unit
def test_config_rtsp_port():
    assert Settings().rtsp_port == 7236


@pytest.mark.unit
def test_config_device_name():
    assert Settings().device_name == 'picast'


@pytest.mark.unit
def test_config_device_type():
    assert Settings().device_type == '7-0050F204-4'


@pytest.mark.unit
def test_config_recreate_group():
    assert Settings().recreate_group == False


@pytest.mark.unit
def test_config_pin():
    assert Settings().pin == '12345678'


@pytest.mark.unit
def test_config_player():
    assert Settings().player == 'vlc'


@pytest.mark.unit
def test_config_player_log_file():
    assert Settings().player_log_file == '/var/tmp/player.log'


@pytest.mark.unit
def test_config_player_custom_args():
    assert Settings().player_custom_args == []


@pytest.mark.unit
def test_config_wps_mode():
    assert Settings().wps_mode == 'pin'


@pytest.mark.unit
def test_config_rtsp_port():
    assert Settings().rtsp_port == 7236


@pytest.mark.unit
def test_config_max_timeout():
    assert Settings().max_timeout == '10'


@pytest.mark.unit
def test_config_gst_decoder():
    assert Settings().gst_decoder == 'omxh264dec'

