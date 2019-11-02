# Configuration for pytest to automatically collect types.
# Thanks to Guilherme Salgado.
import socket

import pytest
from pyannotate_runtime import collect_types


def pytest_collection_finish(session):
    """Handle the pytest collection finish hook: configure pyannotate.
    Explicitly delay importing `collect_types` until all tests have
    been collected.  This gives gevent a chance to monkey patch the
    world before importing pyannotate.
    """
    collect_types.init_types_collection()


@pytest.fixture(autouse=True)
def collect_types_fixture():
    collect_types.start()
    yield
    collect_types.stop()


def pytest_sessionfinish(session, exitstatus):
    collect_types.dump_stats("type_info.json")


@pytest.fixture
def unused_port() -> int:
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    _, port = s.getsockname()
    s.close()
    return port
