"""Tests for the utility functions in the jobs app."""

import pytest

from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.users.models import User


@pytest.mark.django_db()
class TestGetMarnieEmail:
    """Tests for the get_marnie_email utility function."""

    def test_gets_marnie_user_email(self, marnie_user: User) -> None:
        """Test that the email address for Marnie is returned."""
        expected = marnie_user.email
        assert get_marnie_email() == expected

    def test_fails_when_no_marnie_user(self) -> None:
        """Test that an exception is raised when there is no Marnie user."""
        with pytest.raises(User.DoesNotExist, match="No Marnie user found."):
            get_marnie_email()

    def test_fails_when_multiple_marnie_users(
        self,
        marnie_user: User,
        bob_agent_user: User,
    ) -> None:
        """Test that an exception is raised when there are multiple Marnie users."""
        # Grab the bob user, and set his is_marnie to True, to help to trigger this
        # test case.
        bob_agent_user.is_marnie = True
        bob_agent_user.save()

        with pytest.raises(
            User.MultipleObjectsReturned,
            match="Multiple Marnie users found.",
        ):
            get_marnie_email()
