"""management.py command to load initial data into the database for manual testing."""

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from marnies_maintenance_manager.jobs.utils import make_test_user
from marnies_maintenance_manager.users.models import User


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
            make_test_user(User, "david", is_superuser=True)
            self.stdout.write(
                self.style.SUCCESS("Successfully created admin user david"),
            )

    @transaction.atomic
    def create_users_and_data(self) -> None:
        """Create regular users and populate records for each user."""
        # Make the Marnie user.
        if not _user_exists("marnie"):
            make_test_user(User, "marnie", is_marnie=True)
            self.stdout.write(self.style.SUCCESS("Successfully created user marnie"))

        # Make 2 Agent users.
        for name in "bob", "alice":
            if not _user_exists(name):
                make_test_user(User, name, is_agent=True)
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully created user {name}"),
                )

            # Over here we can add some records for each user.


def _user_exists(username: str) -> bool:
    """Check if a user with the given username exists.

    Args:
        username: The username to check.

    Returns:
        True if a user with the given username exists, False otherwise.
    """
    return User.objects.filter(username=username).exists()
