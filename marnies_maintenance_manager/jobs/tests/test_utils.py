"""Tests for the utility functions in the "jobs" app."""

# pylint: disable=unused-argument

import re

import pytest
from _pytest.monkeypatch import MonkeyPatch  # pylint: disable=import-private-name
from django.core.exceptions import ObjectDoesNotExist

from marnies_maintenance_manager.jobs import exceptions
from marnies_maintenance_manager.jobs import utils
from marnies_maintenance_manager.users.models import User


# pylint: disable=no-self-use, magic-value-comparison
@pytest.mark.django_db()
class TestGetMarnieEmail:
    """Tests for the get_marnie_email utility function."""

    def test_gets_marnie_user_email(self, marnie_user: User) -> None:
        """Test that the email address for Marnie is returned.

        Args:
            marnie_user (User): A user instance representing Marnie, expected to be
                                queried.
        """
        expected = marnie_user.email
        assert utils.get_marnie_email() == expected

    def test_fails_when_no_marnie_user(self) -> None:
        """Test that an exception is raised when there is no Marnie user."""
        with pytest.raises(
            exceptions.MarnieUserNotFoundError,
            match="No Marnie user found.",
        ):
            utils.get_marnie_email()

    def test_fails_when_multiple_marnie_users(
        self,
        marnie_user: User,
        bob_agent_user: User,
    ) -> None:
        """Test that an exception is raised when there are multiple Marnie users.

        Args:
            marnie_user (User): A user instance representing Marnie.
            bob_agent_user (User): Another user instance incorrectly flagged as Marnie.
        """
        # Grab the bob user, and set his is_marnie to True, to help to trigger this
        # test case.
        bob_agent_user.is_marnie = True
        bob_agent_user.save()

        with pytest.raises(
            exceptions.MultipleMarnieUsersError,
            match="Multiple Marnie users found.",
        ):
            utils.get_marnie_email()


@pytest.mark.django_db()
class TestGetSystemAdministratorEmail:
    """Tests for the get_sysadmin_email utility function."""

    def test_gets_sysadmin_user_email(self, admin_user: User) -> None:
        """Test that the email address for the system administrator is returned.

        Args:
            admin_user (User): A user instance representing an admin, expected to be
                               queried.
        """
        email = utils.get_sysadmin_email()
        assert email == "admin@example.com"

    def test_fails_when_no_sysadmin_user(self) -> None:
        """Ensure an exception is raised when no system administrator user is found."""
        with pytest.raises(
            exceptions.NoSystemAdministratorUserError,
            match="No system administrator user found.",
        ):
            utils.get_sysadmin_email()

    def test_works_when_there_are_multiple_sysadmin_users(
        self,
        admin_user: User,
        marnie_user: User,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify function operates with multiple sysadmin users and logs a warning.

        Args:
            admin_user (User): A user instance representing an admin.
            marnie_user (User): Another admin user to simulate multiple admins.
            caplog (pytest.LogCaptureFixture): Fixture to capture log outputs.
        """
        # Make Marnie into a sysadmin, in addition to our testing "admin" account,
        # so that we have multiple sysadmins. In that case, we want one of the admin
        # email addresses to be returned, but the system should also log a warning
        # about this.
        marnie_user.is_superuser = True
        marnie_user.save()

        email = utils.get_sysadmin_email()
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
        """Test the logical error handling for impossible sysadmin count.

        Args:
            caplog (pytest.LogCaptureFixture): Fixture to capture log outputs for
                                               critical error logging.
        """
        # Not possible, but going to test for a negative number of sysadmins here,
        # to check the logical error handling.
        msg = "Reached logically impossible branch in get_sysadmin_email"

        with pytest.raises(exceptions.LogicalError, match=re.escape(msg)):
            utils.get_sysadmin_email(_introduce_logic_error=True)

        # Check that this same message was logged at "critical" level.
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert msg in record.message
        assert record.levelname == "CRITICAL"


class TestFirstOrError:
    """Tests for the first_or_error utility function."""

    def test_gets_first_object(self, admin_user: User, marnie_user: User) -> None:
        """Test that the first object in a queryset is returned.

        Args:
            admin_user (User): An admin user included in the queryset.
            marnie_user (User): Another user included in the queryset.
        """
        queryset = User.objects.all()
        first = queryset.first()
        assert utils.first_or_error(queryset) == first

    def test_raises_error_when_queryset_empty(self) -> None:
        """Test that an exception is raised when the queryset is empty."""
        with pytest.raises(ObjectDoesNotExist, match="No object found."):
            utils.first_or_error(User.objects.none())


class TestGetTestUserPassword:
    """Tests for the get_user_password utility function."""

    def test_gets_user_password(self, monkeypatch: MonkeyPatch) -> None:
        """Test that the user password is returned.

        Args:
            monkeypatch (MonkeyPatch): A pytest fixture to patch environment variables.
        """
        varname = "NEW_TEST_PASSWORD"
        password = "the secret"  # noqa: S105
        monkeypatch.setenv(varname, password)
        returned_password = utils.get_test_user_password(key=varname)
        assert returned_password == password

    @staticmethod
    def test_fails_if_env_var_not_set() -> None:
        """Test that an exception is raised when the environment variable is not set."""
        varname = "NEW_TEST_PASSWORD"
        with pytest.raises(
            exceptions.EnvironmentVariableNotSetError,
            match="NEW_TEST_PASSWORD environment variable not set",
        ):
            utils.get_test_user_password(key=varname)


@pytest.mark.django_db()
class TestMakeTestUser:
    """Tests for the make_test_user utility function."""

    @staticmethod
    def test_without_optional_flags() -> None:
        """Test creating a user without any optional flags set."""
        utils.make_test_user(User, "test")

        # Check that the user was created, with all the flags set as expected
        user = User.objects.get(username="test")
        assert user.is_agent is False
        assert user.is_superuser is False
        assert user.is_marnie is False
        assert user.email == "test@example.com"

        email = user.emailaddress_set.first()  # type: ignore[attr-defined]
        assert email.email == "test@example.com"
        assert email.primary is True
        assert email.verified is True

    @staticmethod
    def test_with_all_optional_flags_set_to_none_default_values() -> None:
        """Test creating a user with all optional flags set to none-default values."""
        utils.make_test_user(
            User,
            "test",
            is_agent=True,
            is_superuser=True,
            is_marnie=True,
            email_verified=False,
            email_primary=False,
        )

        # Check that the user was created, with all the flags set as expected
        user = User.objects.get(username="test")
        assert user.is_agent is True
        assert user.is_superuser is True
        assert user.is_marnie is True
        assert user.email == "test@example.com"

        email = user.emailaddress_set.first()  # type: ignore[attr-defined]
        assert email.email == "test@example.com"
        assert email.primary is False
        assert email.verified is False
