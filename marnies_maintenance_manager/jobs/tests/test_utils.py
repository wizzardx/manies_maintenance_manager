"""Tests for the utility functions in the "jobs" app."""

# pylint: disable=no-self-use, magic-value-comparison, redefined-outer-name
# pylint: disable=unused-argument

import re
from unittest import mock

import pytest
import pytest_mock
from _pytest.monkeypatch import MonkeyPatch  # pylint: disable=import-private-name
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest

from marnies_maintenance_manager.jobs import exceptions
from marnies_maintenance_manager.jobs import utils
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import safe_read
from marnies_maintenance_manager.jobs.views.utils import send_quote_update_email
from marnies_maintenance_manager.users.models import User


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
            match="No Marnie user found",
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
            match="Multiple Marnie users found",
        ):
            utils.get_marnie_email()


@pytest.mark.django_db()
class TestGetSystemAdministratorEmail:
    """Tests for the get_sysadmin_email utility function."""

    # noinspection PyUnusedLocal
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
            match="No system administrator user found",
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

    # noinspection PyUnusedLocal
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
        with pytest.raises(ObjectDoesNotExist, match="No object found"):
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
            is_staff=True,
            is_marnie=True,
            email_verified=False,
            email_primary=False,
        )

        # Check that the user was created, with all the flags set as expected
        user = User.objects.get(username="test")
        assert user.is_agent is True
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.is_marnie is True
        assert user.email == "test@example.com"

        email = user.emailaddress_set.first()  # type: ignore[attr-defined]
        assert email.email == "test@example.com"
        assert email.primary is False
        assert email.verified is False


@pytest.fixture()
def job() -> Job:
    """Return a mock of the Job object.

    Returns:
        Job: A mock of the Job object.
    """
    return mock.Mock(spec=Job)


@pytest.fixture()
def http_request() -> HttpRequest:
    """Return a mock of the HttpRequest object.

    Returns:
        HttpRequest: A mock of the HttpRequest object.
    """
    return mock.Mock(spec=HttpRequest)


@mock.patch("marnies_maintenance_manager.jobs.views.utils.EmailMessage")
@mock.patch("marnies_maintenance_manager.jobs.views.utils.get_marnie_email")
@mock.patch("marnies_maintenance_manager.jobs.views.utils.generate_email_body")
def test_send_quote_update_email(
    mock_generate_email_body: mock.Mock,
    mock_get_marnie_email: mock.Mock,
    mock_email_message: mock.Mock,
    http_request: HttpRequest,
    job: Job,
) -> None:
    """Test the send_quote_update_email utility function.

    Args:
        mock_generate_email_body (mock.Mock): Mock of the generate_email_body function.
        mock_get_marnie_email (mock.Mock): Mock of the get_marnie_email function.
        mock_email_message (mock.Mock): Mock of the EmailMessage class.
        http_request (HttpRequest): A mock of the HttpRequest object.
        job (Job): A mock of the Job object.
    """
    # Arrange
    mock_generate_email_body.return_value = "Generated email body"
    mock_get_marnie_email.return_value = "marnie@example.com"
    mock_email_instance = mock.Mock()
    mock_email_message.return_value = mock_email_instance

    job.agent.email = "agent@example.com"
    job.agent.username = "agent_username"
    job.quote.name = "quote.pdf"
    job.quote.read.return_value = b"PDF content"

    email_body = "Initial email body"
    email_subject = "Quote Update"

    # Act
    result = send_quote_update_email(http_request, email_body, email_subject, job)

    # Assert
    mock_generate_email_body.assert_called_once_with(job, http_request)
    mock_get_marnie_email.assert_called_once()

    mock_email_message.assert_called_once_with(
        subject=email_subject,
        body="Initial email bodyGenerated email body",
        from_email="noreply@example.com",
        to=["agent@example.com"],
        cc=["marnie@example.com"],
    )

    mock_email_instance.attach.assert_called_once_with(
        "quote.pdf",
        b"PDF content",
        "application/pdf",
    )
    mock_email_instance.send.assert_called_once()

    assert result == "agent_username"


class TestSafeRead:
    """Tests for the safe_read context manager."""

    @staticmethod
    def test_fails_if_tell_not_at_zero_at_start(
        mocker: pytest_mock.MockFixture,
    ) -> None:
        """Test AssertionError if file pointer isn't reset to 0 at the start.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        file_like = mocker.Mock()
        file_like.tell.return_value = 1
        with (
            pytest.raises(
                AssertionError,
                match="File pointer not reset to 0 before reading.",
            ),
            safe_read(file_like),
        ):
            pass  # pragma: no cover

    @staticmethod
    def test_fails_if_tell_not_at_zero_after_reading(
        mocker: pytest_mock.MockFixture,
    ) -> None:
        """Test AssertionError if file pointer isn't reset to 0 after reading.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        file_like = mocker.Mock()
        file_like.tell.return_value = 0
        file_like.read.return_value = b"PDF content"
        with (
            pytest.raises(
                AssertionError,
                match="File pointer not reset to 0 after reading.",
            ),
            safe_read(file_like),
        ):
            file_like.read.assert_called_once()
        # The 'tell' method should have been called twice by now:
        file_like.tell.assert_has_calls([mocker.call(), mocker.call()])

    @staticmethod
    def test_no_error_when_tell_location_is_a_mock_object(
        mocker: pytest_mock.MockFixture,
    ) -> None:
        """Test that the context manager works when the file pointer is a mock object.

        Args:
            mocker (pytest_mock.MockFixture): A pytest-mock fixture.
        """
        file_like = mocker.Mock()
        file_like.tell.return_value = mocker.Mock()
        file_like.read.return_value = b"PDF content"

        # This code should not raise:
        with safe_read(file_like):
            pass
