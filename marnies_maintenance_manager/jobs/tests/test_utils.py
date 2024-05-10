"""Tests for the utility functions in the jobs app."""

import re

import pytest
from django.core.exceptions import ObjectDoesNotExist

from marnies_maintenance_manager.jobs.exceptions import LogicalError
from marnies_maintenance_manager.jobs.exceptions import MarnieUserNotFoundError
from marnies_maintenance_manager.jobs.exceptions import MultipleMarnieUsersError
from marnies_maintenance_manager.jobs.exceptions import NoSystemAdministratorUserError
from marnies_maintenance_manager.jobs.utils import first_or_error
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.utils import get_sysadmin_email
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
        with pytest.raises(MarnieUserNotFoundError, match="No Marnie user found."):
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
            MultipleMarnieUsersError,
            match="Multiple Marnie users found.",
        ):
            get_marnie_email()


@pytest.mark.django_db()
class TestGetSystemAdministratorEmail:
    """Tests for the get_sysadmin_email utility function."""

    def test_gets_sysadmin_user_email(self, admin_user: User) -> None:
        """Test that the email address for the system administrator is returned."""
        email = get_sysadmin_email()
        assert email == "admin@example.com"

    def test_fails_when_no_sysadmin_user(self) -> None:
        """Ensure an exception is raised when no system administrator user is found."""
        with pytest.raises(
            NoSystemAdministratorUserError,
            match="No system administrator user found.",
        ):
            get_sysadmin_email()

    def test_works_when_there_are_multiple_sysadmin_users(
        self,
        admin_user: User,
        marnie_user: User,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify function operates with multiple sysadmin users and logs a warning."""
        # Make Marnie into a sysadmin, in addition to our testing "admin" account,
        # so that we have multiple sysadmins. In that case, we want one of the admin
        # email addresses to be returned, but the system should also log a warning
        # about this.
        marnie_user.is_superuser = True
        marnie_user.save()

        email = get_sysadmin_email()
        assert email in [admin_user.email, marnie_user.email]

        # We should also log a warning about this.
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert "Multiple system administrator users found." in record.message
        assert "Defaulting to the first user found, with system id: " in record.message

    def test_found_weird_number_of_sysadmin_accounts(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test the logical error handling for impossible sysadmin count."""
        # Not possible, but going to test for a negative number of sysadmins here,
        # to check the logical error handling.
        msg = "Reached logically impossible branch in get_sysadmin_email."

        with pytest.raises(LogicalError, match=re.escape(msg)):
            get_sysadmin_email(_introduce_logic_error=True)

        # Check that this same message was logged at "critical" level.
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert msg in record.message
        assert record.levelname == "CRITICAL"


class TestFirstOrError:
    """Tests for the first_or_error utility function."""

    def test_gets_first_object(self, admin_user: User, marnie_user: User) -> None:
        """Test that the first object in a queryset is returned."""
        queryset = User.objects.all()
        first = queryset.first()
        assert first_or_error(queryset) == first

    def test_raises_error_when_queryset_empty(self) -> None:
        """Test that an exception is raised when the queryset is empty."""
        with pytest.raises(ObjectDoesNotExist, match="No object found."):
            first_or_error(User.objects.none())
