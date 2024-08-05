"""Utility functions for handling date-related operations in functional tests.

This module provides functions to determine and format dates based on system
locale settings, particularly useful for ensuring consistent date inputs
across different testing environments.
"""

# pylint: disable=magic-value-comparison

import re
import subprocess


def get_date_format_from_locale() -> str:
    """Get the date format from the system locale settings.

    Returns:
        str: The date format string.

    Raises:
        RuntimeError: If an error occurs while running the locale command.
        ValueError: If the date format cannot be determined from the locale settings.
    """
    # Run the `locale -k LC_TIME` command
    result = subprocess.run(  # noqa: S603
        ["locale", "-k", "LC_TIME"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )

    # Check for errors
    if result.returncode != 0:
        msg = f"Error running locale command: {result.stderr}"
        raise RuntimeError(msg)

    # Parse the output to find the date format
    output = result.stdout
    date_format = None

    # Look for the d_fmt line which specifies the date format

    # pylint: disable=consider-using-assignment-expr
    match = re.search(r'd_fmt="([^"]+)"', output)
    if match:
        date_format = match.group(1)

    if not date_format:
        msg = "Unable to determine date format from locale settings"
        raise ValueError(msg)

    return date_format


def get_crispy_forms_date_input_format() -> str:
    """Get the date input format used by Crispy Forms.

    Returns:
        str: The date input format string.
    """
    # pylint: disable=consider-using-assignment-expr
    fmt = get_date_format_from_locale().replace("/", "")
    if fmt == "%d%m%Y":
        return "%d%m%Y"

    assert fmt == "%m%d%y"
    return "%m%d%Y"


CRISPY_FORMS_DATE_INPUT_FORMAT = get_crispy_forms_date_input_format()
