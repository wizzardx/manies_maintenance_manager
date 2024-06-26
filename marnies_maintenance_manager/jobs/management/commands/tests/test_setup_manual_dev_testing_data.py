"""Tests for the 'setup_manual_dev_testing_data' command."""

import pytest

from marnies_maintenance_manager.jobs.management.commands.setup_manual_dev_testing_data import (  # noqa: E501
    Command,
)
from marnies_maintenance_manager.users.models import User


@pytest.mark.django_db()
def test_create_admin_user_creates_david_with_admin_panel_access():
    """Ensure the 'david' user is created with access to the admin panel."""
    # Simulate running the admin command:
    cmd = Command()
    cmd.handle()

    # Grab the 'david' user:
    david = User.objects.get(username="david")

    # Check that the 'david' user is set up to be able to access the admin panel:
    assert david.is_superuser is True
    assert david.is_staff is True
