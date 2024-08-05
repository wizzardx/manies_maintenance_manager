"""Common utility functions for functional tests in Marnie's Maintenance Manager.

This module contains general-purpose utility functions that are used across
various test modules. It includes functions for handling timing issues in
browser interactions, such as waiting for elements to become clickable.

Key Functions:
    wait_until: Retry an action until it succeeds or a timeout is reached.
"""

import time
from collections.abc import Callable
from typing import Any

from selenium.common import ElementClickInterceptedException

MAX_WAIT = 5  # Maximum time to wait during retries, before failing the test


def wait_until(fn: Callable[[], Any]) -> Any:
    """Retry an action until it succeeds or the maximum wait time is reached.

    Args:
        fn (Callable[[], Any]): The function to execute and retry.

    Returns:
        Any: The result of the function execution.

    Raises:
        ElementClickInterceptedException: If the element click is intercepted.
    """
    start_time = time.time()
    while True:  # pylint: disable=while-used
        try:
            return fn()
        except ElementClickInterceptedException:  # pragma: no cover
            if time.time() - start_time > MAX_WAIT:
                raise
            time.sleep(0.1)
