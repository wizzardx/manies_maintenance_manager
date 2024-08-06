"""Functional tests for the conftest.py module."""

from unittest.mock import MagicMock
from unittest.mock import patch

from selenium.webdriver.remote.webdriver import WebDriver

from manies_maintenance_manager.functional_tests.conftest import _clear_local_media_dir
from manies_maintenance_manager.functional_tests.conftest import (
    _get_full_window_chrome_browser,
)


# Mocking importlib.import_module for the _get_full_window_chrome_browser function
@patch("importlib.import_module")
@patch("manies_maintenance_manager.functional_tests.conftest.webdriver.Chrome")
def test_get_full_window_chrome_browser(
    mock_chrome: MagicMock,
    mock_import_module: MagicMock,
) -> None:
    """Test that the Chrome browser is returned with the full window size set.

    Args:
        mock_chrome (MagicMock): Pytest-mock MagicMock object.
        mock_import_module (MagicMock): Pytest-mock MagicMock object.
    """
    # Setting up the mock to return a fixed screen size
    mock_pyautogui = MagicMock()
    mock_pyautogui.size.return_value = (1920, 1080)
    mock_import_module.return_value = mock_pyautogui

    driver = MagicMock(spec=WebDriver)
    mock_chrome.return_value = driver

    browser = _get_full_window_chrome_browser()

    # Assertions to verify the window size is set correctly
    driver.set_window_size.assert_called_once_with(1920, 1080)

    # Assertion to ensure the correct driver is returned
    assert isinstance(browser, WebDriver)


# Mocking the Path.iterdir and Path.unlink for _clear_local_media_dir function
@patch("manies_maintenance_manager.functional_tests.conftest.Path.iterdir")
def test_clear_local_media_dir(mock_iterdir: MagicMock) -> None:
    """Unlink files with 'test' in the name from the local media directory only.

    Args:
        mock_iterdir (MagicMock): Pytest-mock MagicMock object.
    """
    # Creating a mock path and mock files
    mock_test_file = MagicMock()
    mock_test_file.name = "test_file.pdf"

    mock_non_test_file = MagicMock()
    mock_non_test_file.name = "regular_file.pdf"

    mock_media_type_dir = MagicMock()
    mock_media_type_dir.iterdir.return_value = [mock_test_file, mock_non_test_file]

    mock_base_media_dir = MagicMock()
    mock_base_media_dir.iterdir.return_value = [mock_media_type_dir]

    mock_iterdir.return_value = mock_base_media_dir.iterdir()

    # Calling the function
    _clear_local_media_dir()

    # Assertions to verify the file with 'test' in the name is unlinked
    mock_test_file.unlink.assert_called_once()

    # Assertions to verify the file without 'test' in the name is not unlinked
    mock_non_test_file.unlink.assert_not_called()
