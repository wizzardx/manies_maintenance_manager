"""management.py command to load initial data into the database for manual testing."""

import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from marnies_maintenance_manager.jobs.tests.utils import make_test_user
from marnies_maintenance_manager.users.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to load initial data into the database for manual testing."""

    help = "Load initial data into the database"

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """Handle the command.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.create_admin_user()
        self.create_users_and_data()

    @transaction.atomic
    def create_admin_user(self) -> None:
        """Create an admin user if it does not exist."""
        if not _user_exists("david"):
            make_test_user(User, "david", is_superuser=True, is_staff=True)
            self.stdout.write(
                self.style.SUCCESS("Successfully created admin user david"),
            )
        else:
            logging.debug("Admin user david already exists")

    @transaction.atomic
    def create_users_and_data(self) -> None:
        """Create regular users and populate records for each user."""
        # Make the Marnie user.
        if not _user_exists("marnie"):
            make_test_user(User, "marnie", is_marnie=True)
            self.stdout.write(self.style.SUCCESS("Successfully created user marnie"))
        else:
            logging.debug("User marnie already exists")

        # Make 2 Agent users.
        for name in "bob", "alice":
            if not _user_exists(name):
                make_test_user(User, name, is_agent=True)
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully created user {name}"),
                )
            else:
                logging.debug("User %s already exists", name)

            # Over here we can add some records for each user.


def _user_exists(username: str) -> bool:
    """Check if a user with the given username exists.

    Args:
        username: The username to check.

    Returns:
        True if a user with the given username exists, False otherwise.
    """
    return User.objects.filter(username=username).exists()
