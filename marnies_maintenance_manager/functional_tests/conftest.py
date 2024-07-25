"""Fixtures for the functional tests of the Marnie's Maintenance Manager project."""

# pylint: disable=unused-argument

import importlib
from collections.abc import Generator
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import environ
import pytest
from pytest_django import DjangoDbBlocker
from pytest_django.live_server_helper import LiveServer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.jobs.models import Job

env = environ.Env()


USE_BROWSER_IN_DOCKER = env.bool("USE_BROWSER_IN_DOCKER", True)


def _get_browser_in_docker() -> WebDriver:
    """Get a WebDriver instance for use in a Docker environment.

    Returns:
        WebDriver: A WebDriver instance for use in tests.
    """
    options = Options()
    # You can add more options here if needed
    return webdriver.Remote(
        command_executor="http://chrome:4444/wd/hub",
        options=options,
    )


def _get_full_window_chrome_browser() -> WebDriver:
    """Get a WebDriver instance for use in a non-Docker environment.

    Returns:
        WebDriver: A WebDriver instance for use in tests.
    """
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    # Get the screen resolution

    # Dynamically import pyautogui
    pyautogui = importlib.import_module("pyautogui")

    screen_width, screen_height = pyautogui.size()

    # Resize the window to the screen resolution
    driver.set_window_size(screen_width, screen_height)

    return driver


@pytest.fixture()
def browser() -> Iterator[WebDriver]:
    """Provide a configured Selenium WebDriver for testing in a Docker environment.

    Yields:
        WebDriver: A WebDriver instance for use in tests, ensuring it's closed
                   afterward.
    """
    # pylint: disable=consider-using-assignment-expr, consider-ternary-expression
    if USE_BROWSER_IN_DOCKER:
        driver = _get_browser_in_docker()
    else:  # pragma: no cover
        driver = _get_full_window_chrome_browser()

    yield driver

    driver.quit()


def _delete_ft_test_data() -> None:
    # Remove all 'Job's that have 'gps' detail:
    # "https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7" # noqa: ERA001
    # - this is the detail that is unique to the FTs
    Job.objects.filter(gps_link="https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7").delete()


def _clear_local_media_dir() -> None:
    # Clear the local media directory
    # I don't like files like this collecting locally:
    # ./ marnies_maintenance_manager / private-media / quotes /
    #        Discovery_PMB_2024_1.pdf
    # ./ marnies_maintenance_manager / private-media / quotes /
    #        test_5fc6fj3.pdf
    # ./ marnies_maintenance_manager / private-media / quotes /
    #        test.pdf
    # ./ marnies_maintenance_manager / private-media / quotes /
    #        test_WRv04By.pdf
    # ./ marnies_maintenance_manager / private-media / quotes /
    #        test_FdO9dtI.pdf
    base_media_dir = Path("marnies_maintenance_manager/private-media")
    for media_type_dir in base_media_dir.iterdir():
        for file in media_type_dir.iterdir():
            # Only remove files with 'test' in the name - those are probably
            # ones used for functional testing. Others are probably ones I'm
            # using for manual testing.
            if "test" in file.name:  # pylint: disable=magic-value-comparison
                file.unlink()


@pytest.fixture(autouse=True)
def _tidy_test_records(
    django_db_blocker: DjangoDbBlocker,
) -> Generator[None, None, None]:
    """Tidy up test records before and after the functional tests.

    Args:
        django_db_blocker: A fixture to block the Django database.

    Yields:
        None: A dummy value.
    """
    # Delete any FT-specific test data present before the start of the tests:
    with django_db_blocker.unblock():
        _delete_ft_test_data()
    _clear_local_media_dir()

    yield

    # Delete any FT-specific test data present after the end of the tests:
    with django_db_blocker.unblock():
        _delete_ft_test_data()
    _clear_local_media_dir()


TEST_SERVER = cast(str | None, env.str("TEST_SERVER", None))

# pylint: disable=consider-using-assignment-expr
if TEST_SERVER:
    # pragma: no cover

    @pytest.fixture()  # pragma: no cover
    # pylint: disable=redefined-outer-name
    def live_server_url(_tidy_test_records: None) -> str:  # pragma: no cover
        """Return the URL of the test server.

        Returns:
            str: The URL of the test server.
        """
        assert isinstance(TEST_SERVER, str)  # pragma: no cover
        return "http://" + TEST_SERVER  # pragma: no cover

else:

    @pytest.fixture()
    # pylint: disable=redefined-outer-name
    def live_server_url(live_server: LiveServer, _tidy_test_records: None) -> str:
        """Return the URL of the test server.

        Args:
            live_server: A fixture to provide a live server.

        Returns:
            str: The URL of the test server.
        """
        return live_server.url.replace("0.0.0.0", "django")  # noqa: S104


DATABASE_IS_EXISTING_EXTERNAL = env.bool("DATABASE_IS_EXISTING_EXTERNAL", False)

# pylint: disable=consider-using-assignment-expr
if DATABASE_IS_EXISTING_EXTERNAL:

    @pytest.fixture(scope="session")  # pragma: no cover
    def django_db_setup() -> None:  # noqa: PT004  # pragma: no cover
        """Ensure the database is not created or destroyed by Django."""
        # As per the guide here:
        # https://pytest-django.readthedocs.io/en/latest/database.html#using-an-existing-external-database-for-tests
