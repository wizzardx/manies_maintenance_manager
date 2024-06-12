"""Test utility functions used by both the functional tests and the other tests.

By other tests, I mean the unit tests and the integration tests.

"""

from collections.abc import Generator
from contextlib import contextmanager

import pytest


@contextmanager
def suppress_fastdev_strict_if_deprecation_warning() -> Generator[None, None, None]:
    """Context manager to suppress a specific FASTDEV_STRICT_IF deprecation warning.

     Django-FastDev causes a DeprecationWarning to be logged when using the
     # {% if %} template tag. This is somewhere deep within the Django-Allauth package,
     # while handling a GET request to the /accounts/login/ URL. We can ignore this
     # for our testing.

    Example:
         >>> with suppress_fastdev_strict_if_deprecation_warning():
         ...     import warnings
         ...     warnings.warn("set FASTDEV_STRICT_IF in settings, and use "
         ...                   "{% ifexists %} instead of {% if %}", DeprecationWarning)

     Yields:
         None: The context manager does not return anything.
    """
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        yield
