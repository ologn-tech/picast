import os
from logging import config as LoggingConfig

from picast.settings import Settings

import pytest


@pytest.mark.unit
def test_logging_config():
    LoggingConfig.fileConfig(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'picast', 'logging.ini'))

@pytest.mark.unit
def test_config_init_config():
    config = Settings(config=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'picast', 'settings.ini'))
    assert config.inifile == os.path.join(os.path.dirname(os.path.dirname(__file__)), 'picast', 'settings.ini')

@pytest.mark.unit
def test_config_logger():
    assert Settings().logger == 'picast'


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
    assert Settings().device_type == '7-0050F204-1'


@pytest.mark.unit
def test_config_group_name():
    assert Settings().group_name == 'persistent'


@pytest.mark.unit
def test_config_pin():
    assert Settings().pin == '12345678'
