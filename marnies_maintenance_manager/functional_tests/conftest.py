"""Fixtures for the functional tests of the Marnie's Maintenance Manager project."""

from collections.abc import Iterator

import pytest
from pytest_django.live_server_helper import LiveServer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver


@pytest.fixture()
def browser() -> Iterator[WebDriver]:
    """Provide a configured Selenium WebDriver for testing in a Docker environment.

    Yields:
        WebDriver: A WebDriver instance for use in tests, ensuring it's closed
                   afterward.
    """
    options = Options()
    # You can add more options here if needed
    driver = webdriver.Remote(
        command_executor="http://chrome:4444/wd/hub",
        options=options,
    )

    yield driver

    driver.quit()


@pytest.fixture()
def live_server_url(live_server: LiveServer) -> str:
    """Modify the live_server URL to use 'django' instead of '0.0.0.0'.

    Args:
        live_server (LiveServer): The pytest-django fixture providing a live server.

    Returns:
        str: The modified URL as a string.
    """
    return live_server.url.replace("0.0.0.0", "django")  # noqa: S104
