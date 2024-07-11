"""Functional tests for the utility functions in the utils module."""

from collections.abc import Callable

# pylint: disable=magic-value-comparison, redefined-outer-name
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from marnies_maintenance_manager.functional_tests.utils import (
    get_crispy_forms_date_input_format,
)
from marnies_maintenance_manager.functional_tests.utils import (
    get_date_format_from_locale,
)


# Mock the subprocess.run function to simulate different command outputs and return
# codes
@pytest.fixture()
def mock_subprocess_run(mocker: MockerFixture) -> Callable[..., MagicMock]:
    """Fixture to mock the subprocess.run function.

    Args:
        mocker (MockerFixture): Pytest-mock mocker fixture.

    Returns:
        Callable[..., MagicMock]: Function to mock the "subprocess.run" function.
    """

    def _mock_run(output: str = "", returncode: int = 0, stderr: str = "") -> MagicMock:
        mock = mocker.patch("subprocess.run")
        mock.return_value.stdout = output
        mock.return_value.returncode = returncode
        mock.return_value.stderr = stderr
        return mock

    return _mock_run


# Test case for get_date_format_from_locale with successful locale command execution
def test_get_date_format_from_locale_success(
    mock_subprocess_run: Callable[..., MagicMock],
) -> None:
    """Ensure the date format is correctly extracted from the locale command output.

    Args:
        mock_subprocess_run (Callable[..., MagicMock]): Pytest fixture to mock the
            "subprocess.run" function.
    """
    mock_subprocess_run(output='d_fmt="%d/%m/%Y"\n')
    assert get_date_format_from_locale() == "%d/%m/%Y"


# Test case for get_date_format_from_locale with locale command failure
def test_get_date_format_from_locale_runtime_error(
    mock_subprocess_run: Callable[..., MagicMock],
) -> None:
    """Test that a RuntimeError is raised when the locale command fails.

    Args:
        mock_subprocess_run (Callable[..., MagicMock]): Pytest fixture to mock the
            "subprocess.run" function
    """
    mock_subprocess_run(returncode=1, stderr="Locale command failed")
    with pytest.raises(
        RuntimeError,
        match="Error running locale command: Locale command failed",
    ):
        get_date_format_from_locale()


# Test case for get_date_format_from_locale with no date format found
def test_get_date_format_from_locale_value_error(
    mock_subprocess_run: Callable[..., MagicMock],
) -> None:
    """Test that a ValueError is raised when the date format cannot be determined.

    Args:
        mock_subprocess_run (Callable[..., MagicMock]): Pytest fixture to mock the
            "subprocess.run" function.
    """
    mock_subprocess_run(output="no_date_format_here\n")
    with pytest.raises(
        ValueError,
        match="Unable to determine date format from locale settings",
    ):
        get_date_format_from_locale()


# Test case for get_crispy_forms_date_input_format with format %d/%m/%Y
def test_get_crispy_forms_date_input_format_ddmmyyyy(mocker: MockerFixture) -> None:
    """Test that the date format is correctly converted from %d/%m/%Y to %d%m%Y.

    Args:
        mocker (MockerFixture): Pytest-mock mocker fixture.
    """
    mocker.patch(
        "marnies_maintenance_manager.functional_tests.utils.get_date_format_from_locale",
        return_value="%d/%m/%Y",
    )
    assert get_crispy_forms_date_input_format() == "%d%m%Y"


# Test case for get_crispy_forms_date_input_format with format %m/%d/%Y
def test_get_crispy_forms_date_input_format_mmddyyyy(mocker: MockerFixture) -> None:
    """Test that the date format is correctly converted from %m/%d/%Y to %m%d%Y.

    Args:
        mocker (MockerFixture): Pytest-mock mocker fixture.
    """
    mocker.patch(
        "marnies_maintenance_manager.functional_tests.utils.get_date_format_from_locale",
        return_value="%m/%d/%y",
    )
    assert get_crispy_forms_date_input_format() == "%m%d%Y"


# Test case for get_crispy_forms_date_input_format with unexpected format
def test_get_crispy_forms_date_input_format_unexpected_format(
    mocker: MockerFixture,
) -> None:
    """Test that an AssertionError is raised when an unexpected date format is returned.

    Args:
        mocker (MockerFixture): Pytest-mock mocker fixture.
    """
    mocker.patch(
        "marnies_maintenance_manager.functional_tests.utils.get_date_format_from_locale",
        return_value="%Y/%m/%d",
    )
    with pytest.raises(AssertionError):
        get_crispy_forms_date_input_format()
