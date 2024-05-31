# noqa: INP001

"""Library to clear the pytest lastfailed file under certain conditions."""

# pylint: disable=else-if-used,confusing-consecutive-elif

import json
from pathlib import Path

LASTFAILED_PATH = Path(".pytest_cache/v/cache/lastfailed")


def clear_file(
    *,
    clear_when_functional_test: bool = False,
    clear_when_not_functional_test: bool = False,
) -> None:
    """Remove the pytest lastfailed file under the requested conditions.

    Args:
        clear_when_functional_test (bool): Whether to clear the file if it is
            functional test related.
        clear_when_not_functional_test (bool): Whether to clear the file if it is
            not functional test related.

    Raises:
        ValueError: If neither condition is set to True.
        ValueError: If both conditions are set to True.
    """
    # At least one of the conditions must be True:
    if not clear_when_functional_test and not clear_when_not_functional_test:
        msg = "At least one of the conditions must be True"
        raise ValueError(msg)

    # Both cannot be set to True:
    if clear_when_functional_test and clear_when_not_functional_test:
        msg = "Both conditions cannot be set to True"
        raise ValueError(msg)

    # Quit if the pytest lastfailed file does not exist:
    if not LASTFAILED_PATH.is_file():
        return

    # Read the contents. It's a dictionary mapping between paths and boolean values.
    with LASTFAILED_PATH.open(encoding="utf-8") as f:
        j = json.load(f)

    # If any of the lines contain "/functional_tests/", then we consider this to be
    # a functional test-related config
    is_functional_test_cfg = False
    for key in j:
        if "/functional_tests/" in key:  # pylint: disable=magic-value-comparison
            is_functional_test_cfg = True
            break

    do_clear = False
    if is_functional_test_cfg:
        # Functional test config
        if clear_when_functional_test:
            do_clear = True
    elif clear_when_not_functional_test:
        do_clear = True

    if do_clear:
        print(f"Removing now-unrelated config file at {LASTFAILED_PATH}.")  # noqa: T201
        LASTFAILED_PATH.unlink()
