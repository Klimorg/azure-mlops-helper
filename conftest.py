import pytest
from _pytest.logging import LogCaptureFixture
from loguru import logger


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    """
    Make pytest work with loguru. See:
    https://loguru.readthedocs.io/en/stable/resources/migration.html#making-things-work-with-pytest-and-caplog
    """
    handler_id = logger.add(caplog.handler, format="{message}")
    yield caplog
    logger.remove(handler_id)
