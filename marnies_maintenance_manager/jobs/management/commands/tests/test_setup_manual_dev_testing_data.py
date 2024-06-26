"""Tests for the 'setup_manual_dev_testing_data' command."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture  # pylint: disable=import-private-name

from marnies_maintenance_manager.jobs.management.commands import (
    setup_manual_dev_testing_data,
)
from marnies_maintenance_manager.users.models import User

Command = setup_manual_dev_testing_data.Command


@pytest.mark.django_db()
def test_create_admin_user_creates_david_with_admin_panel_access() -> None:
    """Ensure the 'david' user is created with access to the admin panel."""
    # Simulate running the admin command:
    cmd = Command()
    cmd.handle()

    # Grab the 'david' user:
    david = User.objects.get(username="david")

    # Check that the 'david' user is set up to be able to access the admin panel:
    assert david.is_superuser is True
    assert david.is_staff is True


@pytest.mark.django_db()
def test_running_command_twice_causes_user_already_exists_messages_to_be_logged(
    caplog: LogCaptureFixture,
) -> None:
    """Ensure command logs user already exists messages when run twice.

    Args:
        caplog (LogCaptureFixture): The fixture to capture log messages.
    """
    cmd = Command()
    cmd.handle()

    # Set log level to DEBUG here to capture just the debug messages from the second
    # time that the command is run:
    caplog.set_level(logging.DEBUG)
    cmd.handle()

    assert caplog.messages == [
        "Admin user david already exists",
        "User marnie already exists",
        "User bob already exists",
        "User alice already exists",
    ]
