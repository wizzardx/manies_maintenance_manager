"""Tests for the conftest.py file in the project root."""

# pylint: disable=too-few-public-methods

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import pytest_mock

from marnies_maintenance_manager.jobs.conftest_in_project_root import load_test_results
from marnies_maintenance_manager.jobs.conftest_in_project_root import (
    pytest_runtest_makereport,
)


class TestLoadResults:
    """Tests for the load_test_results function."""

    @staticmethod
    def test_returns_empty_dict_when_file_does_not_exist() -> None:
        """Test that an empty dictionary is returned when the file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_file = Path(tmpdir) / "no_such_file.json"
            assert load_test_results(non_existent_file) == {}


class TestPytestRunTestMakeReport:
    """Tests for the pytest_runtest_makereport function."""

    @staticmethod
    def test_adds_default_test_result_to_session(
        mocker: pytest_mock.MockFixture,
    ) -> None:
        """Test that a default test result is added to the session.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.q
        """
        gen, test_results = setup_mock_pytest_runtest(mocker)

        mock_report = mocker.Mock(
            when="call",
            nodeid="<TEST_NODE_ID>",
            failed=False,
            passed=False,
        )
        mock_outcome = mocker.Mock()
        mock_outcome.get_result.return_value = mock_report

        with pytest.raises(StopIteration):
            gen.send(mock_outcome)

        # Check that we have added the default test result to the session
        assert test_results == {
            "<TEST_NODE_ID>": {"passed": 0, "failed": 0, "last_failed": None},
        }

    @staticmethod
    def test_failed_test_result_to_session(mocker: pytest_mock.MockFixture) -> None:
        """Test that a failed test result is added to the session.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        # Make a standalone (not patched) mock "now" function, with the real now method
        # as a schema, where you can pass UTC on it, call isoformat on it, and return a
        # test string "FAKE_TIME"
        mock_now = mocker.Mock()
        mock_now.return_value.isoformat.return_value = "<MOCK_TIME_ISOFORMAT>"

        test_results: dict[str, Any] = {}
        mock_session = mocker.Mock(test_results=test_results)
        mock_item = mocker.Mock(session=mock_session)
        mock_call = mocker.Mock()
        gen = pytest_runtest_makereport(item=mock_item, call=mock_call, now=mock_now)
        next(gen)

        mock_report = mocker.Mock(
            when="call",
            nodeid="<TEST_NODE_ID>",
            failed=True,
            passed=False,
        )
        mock_outcome = mocker.Mock()
        mock_outcome.get_result.return_value = mock_report

        with pytest.raises(StopIteration):
            gen.send(mock_outcome)

        # Check that we have added the default test result to the session
        assert test_results == {
            "<TEST_NODE_ID>": {
                "failed": 1,
                "last_failed": "<MOCK_TIME_ISOFORMAT>",
                "passed": 0,
            },
        }

    @staticmethod
    def test_passed_test_result_to_session(mocker: pytest_mock.MockFixture) -> None:
        """Test that a passed test result is added to the session.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        gen, test_results = setup_mock_pytest_runtest(mocker)

        mock_report = mocker.Mock(
            when="call",
            nodeid="<TEST_NODE_ID>",
            failed=False,
            passed=True,
        )
        mock_outcome = mocker.Mock()
        mock_outcome.get_result.return_value = mock_report

        with pytest.raises(StopIteration):
            gen.send(mock_outcome)

        # Check that we have added the default test result to the session
        assert test_results == {
            "<TEST_NODE_ID>": {"passed": 1, "failed": 0, "last_failed": None},
        }


def setup_mock_pytest_runtest(
    mocker: pytest_mock.MockFixture,
) -> tuple[Generator[None, Any, None], dict[str, dict[str, int | None]]]:
    """Set up mock objects for `pytest_runtest_makereport` tests.

    Args:
        mocker (pytest_mock.MockFixture): A pytest-mock fixture.

    Returns:
        tuple[Generator[None, Any, None], dict[str, dict[str, int | None]]]: A tuple
            containing the generator and the "test results" dictionary.
    """
    test_results: dict[str, Any] = {}
    mock_session = mocker.Mock(test_results=test_results)
    mock_item = mocker.Mock(session=mock_session)
    mock_call = mocker.Mock()
    gen = pytest_runtest_makereport(mock_item, mock_call)
    next(gen)
    return gen, test_results
