"""Configuration for pytest.

This module contains pytest hooks for customizing the test collection and execution
order based on file modification times and test result history.

Functionality:
1. Load and save test results to a JSON file.
2. Track the number of times each test has passed or failed, and the last time it
    failed.
3. Sort test files by modification time, and within those files, sort tests by the most
    recent failures.

Hooks:
- pytest_sessionstart: Loads test results at the beginning of the test session.
- pytest_sessionfinish: Saves test results at the end of the test session.
- pytest_runtest_makereport: Records the outcome of each test.
- pytest_collection_modifyitems: Modifies the order of test collection.

Usage:
    Place this conftest.py file in your test directory. pytest will automatically
    discover and use it.
"""

# pylint: disable=magic-value-comparison

import json
from collections.abc import Callable
from collections.abc import Generator
from datetime import UTC
from datetime import datetime
from datetime import tzinfo
from pathlib import Path
from typing import Any

import pytest
from typeguard import check_type

# Path to the file that will store test results
TEST_RESULTS_FILE = Path("test_results.json")


def load_test_results(path: Path = TEST_RESULTS_FILE) -> dict[str, dict[str, Any]]:
    """Load test results from a JSON file.

    Args:
        path (Path): The path to the JSON file.

    Returns:
        dict[str, dict[str, Any]]: The test results.
    """
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return check_type(json.load(f), dict[str, dict[str, Any]])
    return {}


def save_test_results(results: dict[str, dict[str, Any]]) -> None:
    """Save test results to a JSON file.

    Args:
        results (dict[str, dict[str, Any]]): The test results to save.
    """
    with TEST_RESULTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session: pytest.Session) -> None:
    """Load test results at the start of the session.

    Args:
        session (pytest.Session): The pytest session object.
    """
    session.test_results = load_test_results()  # type: ignore[attr-defined]


# noinspection PyUnusedLocal
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,  # pylint: disable=unused-argument
) -> None:
    """Save test results at the end of the session.

    Args:
        session (pytest.Session): The pytest session object.
        exitstatus (int): The exit status of the session.
    """
    test_results: dict[str, dict[str, Any]] = session.test_results  # type: ignore[attr-defined]
    save_test_results(test_results)


# noinspection PyUnusedLocal
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[Any],  # pylint: disable=unused-argument
    now: Callable[[tzinfo | None], datetime] = datetime.now,
) -> Generator[None, Any, None]:
    """Track test results (passed or failed) and record them.

    Args:
        item (pytest.Item): The test item.
        call (pytest.CallInfo): The call information.
        now (Callable[[tzinfo | None], datetime]): A function that returns the current
            time.

    Yields:
        Generator[None, Any, None]: The generator.
    """
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        nodeid: str = report.nodeid
        session: pytest.Session = item.session
        test_results: dict[str, dict[str, Any]] = session.test_results  # type: ignore[attr-defined]
        if nodeid not in test_results:
            test_results[nodeid] = {
                "passed": 0,
                "failed": 0,
                "last_failed": None,
            }
        if report.failed:
            test_results[nodeid]["failed"] += 1
            test_results[nodeid]["last_failed"] = now(
                UTC,
            ).isoformat()
        elif report.passed:
            test_results[nodeid]["passed"] += 1


# noinspection PyUnusedLocal
def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,  # pylint: disable=unused-argument
    items: list[pytest.Item],
) -> None:
    """Sort test items first by file modification time and then by last failure time.

    Args:
        session (pytest.Session): The pytest session object.
        config (pytest.Config): The pytest config object.
        items (list[pytest.Item]): The list of test items.
    """
    # Sort by modification time of the file
    items.sort(key=lambda item: Path(item.fspath).stat().st_mtime, reverse=True)

    # Sort within each file by last failure time
    def get_failure_time(item: pytest.Item) -> datetime:
        nodeid: str = item.nodeid
        test_results: dict[str, dict[str, Any]] = session.test_results  # type: ignore[attr-defined]

        test_result: dict[str, Any] | None = test_results.get(
            nodeid,
        )
        last_failed: str | None = (
            test_result.get("last_failed") if test_result else None
        )
        return (
            datetime.fromisoformat(last_failed)
            if last_failed
            else datetime.min.replace(tzinfo=UTC)
        )

    items.sort(key=get_failure_time, reverse=True)
