"""Unit tests for the job create view."""

# pylint: disable=magic-value-comparison,no-self-use,unused-argument,too-many-arguments

from typing import cast

import pytest
from bs4 import BeautifulSoup
from django.contrib.messages.storage.base import Message
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.utils import (
    check_basic_page_html_structure,
)
from marnies_maintenance_manager.jobs.utils import get_sysadmin_email
from marnies_maintenance_manager.jobs.views import JobCreateView
from marnies_maintenance_manager.jobs.views import JobListView
from marnies_maintenance_manager.users.models import User


def test_creating_a_new_job_sets_an_agent_from_the_request(
    bob_agent_user_client: Client,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """Creating a job should automatically assign the agent from the request.

    Args:
        bob_agent_user_client (Client): Client used by Bob, an agent user.
        bob_agent_user (User): Bob's user instance, an agent.
        marnie_user (User): Marnie's user instance, used for validation in this test.
    """
    client = bob_agent_user_client
    response = client.post(
        reverse("jobs:job_create"),
        {
            "date": "2022-01-01",
            "address_details": "1234 Main St, Springfield, IL",
            "gps_link": "https://www.google.com/maps",
            "quote_request_details": "Replace the kitchen sink",
        },
    )
    assert response.status_code == status.HTTP_302_FOUND
    job = Job.objects.first()
    assert job is not None
    assert job.agent == bob_agent_user


class TestOnlyLoggedInUsersCanAccessJobCreateView:
    """Ensure only logged-in users can access the job create view."""

    @pytest.mark.django_db()
    def test_anonymous_login_fails_to_access_job_create_view(
        self,
        client: Client,
    ) -> None:
        """Verify that anonymous users cannot access the job create view.

        Args:
            client (Client): A test client for an anonymous user.
        """
        response = client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_302_FOUND

    def test_bob_agent_user_can_access_job_create_view(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure Bob the agent can access the job create view.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
        """
        response = bob_agent_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK


class TestJobCreateViewCanOnlyBeReachedByAgentsAndSuperuser:
    """Ensure job create view access is restricted to agents and superusers."""

    @pytest.mark.django_db()
    def test_access_by_anonymous_user_is_denied(self, client: Client) -> None:
        """Verify that anonymous users cannot access the job create view.

        Args:
            client (Client): A test client for an anonymous user.
        """
        response = client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_302_FOUND

    def test_access_by_marnie_user_is_denied(self, marnie_user_client: Client) -> None:
        """Test that Marnie cannot access the job create view.

        Args:
            marnie_user_client (Client): A test client configured for Marnie.
        """
        response = marnie_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_by_bob_agent_user_is_allowed(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """Confirm Bob the agent can access the job create view.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an
                                            agent user.
        """
        response = bob_agent_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK

    def test_access_by_peter_agent_user_is_allowed(
        self,
        peter_agent_user_client: Client,
    ) -> None:
        """Confirm that Peter the agent can access the job create view.

        Args:
            peter_agent_user_client (Client): A test client configured for Peter, an
                                              agent user.
        """
        response = peter_agent_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK

    def test_access_by_superuser_user_is_allowed(
        self,
        superuser_client: Client,
    ) -> None:
        """Test that a superuser can access the job create view.

        Args:
            superuser_client (Client): A test client with superuser permissions.
        """
        response = superuser_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK


def test_create_job_form_uses_date_type_for_date_input_field(
    bob_agent_user_client: Client,
) -> None:
    """Ensure the job create form uses an HTML5 date input for the date field.

    Args:
        bob_agent_user_client (Client): A test client configured for Bob, an agent user.
    """
    response = bob_agent_user_client.get(reverse("jobs:job_create"))
    form = response.context["form"]
    date_widget = form.fields["date"].widget
    assert date_widget.input_type == "date"


class TestAgentCreatingAJobShowsThemFlashMessages:
    """Test that agents see flash messages when creating a job."""

    def test_a_success_flash_message(
        self,
        bob_agent_user_client: Client,
        marnie_user: User,
    ) -> None:
        """Ensure agents see a success message when a job is successfully created.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
            marnie_user (User): Marnie's user instance, included for context in tests.
        """
        flashed_message = _get_flashed_message_after_creating_a_job(
            bob_agent_user_client,
        )
        assert (
            flashed_message.message
            == "Your maintenance request has been sent to Marnie."
        )
        assert flashed_message.level_tag == "success"

    def test_error_flash_when_no_marnie_user_exists(
        self,
        bob_agent_user_client: Client,
        caplog: pytest.LogCaptureFixture,
        superuser_user: User,
    ) -> None:
        """Test that agents see an error message when no Marnie user exists.

        Args:
            bob_agent_user_client (Client): A test client for Bob, an agent user.
            caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
            superuser_user (User): A superuser instance used for additional validation.
        """
        expected_flashed_message = (
            "No Marnie user found.\n"
            "Unable to send maintenance request email.\n"
            "Please contact the system administrator at " + get_sysadmin_email()
        )
        expected_logged_error = (
            "No Marnie user found. Unable to send maintenance request email."
        )

        _check_creating_a_job_flashes_and_logs_errors(
            bob_agent_user_client,
            caplog,
            expected_flashed_message,
            expected_logged_error,
        )

    def test_error_flash_when_agent_user_has_no_email_address(  # noqa: PLR0913
        self,
        bob_agent_user_client: Client,
        bob_agent_user: User,
        caplog: pytest.LogCaptureFixture,
        superuser_user: User,
        marnie_user: User,
    ) -> None:
        """Test that agents see an error message when their user has no email address.

        Args:
            bob_agent_user_client (Client): A test client for Bob, an agent user.
            bob_agent_user (User): Bob's user instance, used for validation in this
                                   test.
            caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
            marnie_user (User): Marnie's user instance, used for validation in this
                                test.
            superuser_user (User): A superuser instance used for additional validation.
        """
        bob_agent_user.email = ""
        bob_agent_user.save()

        expected_flashed_message = (
            "Your email address is missing.\n"
            "Unable to send maintenance request email.\n"
            "Please contact the system administrator at " + get_sysadmin_email()
        )
        expected_logged_error = (
            "User bob has no email address. Unable to send maintenance request email."
        )

        _check_creating_a_job_flashes_and_logs_errors(
            bob_agent_user_client,
            caplog,
            expected_flashed_message,
            expected_logged_error,
        )

    def test_error_flash_when_marnie_user_has_no_email_address(  # noqa: PLR0913
        self,
        bob_agent_user_client: Client,
        bob_agent_user: User,
        caplog: pytest.LogCaptureFixture,
        superuser_user: User,
        marnie_user: User,
    ) -> None:
        """Test that agents see an error message when Marnie has no email address.

        Args:
            bob_agent_user_client (Client): A test client for Bob, an agent user.
            bob_agent_user (User): Bob's user instance, used for validation in this
                                   test.
            caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
            marnie_user (User): Marnie's user instance, used for validation in this
                                test.
            superuser_user (User): A superuser instance used for additional validation.
        """
        marnie_user.email = ""
        marnie_user.save()

        expected_flashed_message = (
            "Marnie's email address is missing.\n"
            "Unable to send maintenance request email.\n"
            "Please contact the system administrator at " + get_sysadmin_email()
        )
        expected_logged_error = (
            "User marnie has no email address. "
            "Unable to send maintenance request email."
        )

        _check_creating_a_job_flashes_and_logs_errors(
            bob_agent_user_client,
            caplog,
            expected_flashed_message,
            expected_logged_error,
        )

    def test_error_flash_when_agent_user_email_address_not_verified(  # noqa: PLR0913
        self,
        bob_agent_user_without_verified_email_client: Client,
        bob_agent_user_without_verified_email: User,
        caplog: pytest.LogCaptureFixture,
        superuser_user: User,
        marnie_user: User,
    ) -> None:
        """Test that agents see an error message when their email is not verified.

        Args:
            bob_agent_user_without_verified_email_client (Client): A test client for
                Bob, an agent user without a verified email address.
            bob_agent_user_without_verified_email (User): Bob's user instance without a
                verified email address.
            caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
            marnie_user (User): Marnie's user instance, used for validation in this
                               test.
            superuser_user (User): A superuser instance used for additional validation.
        """
        expected_flashed_message = (
            "Your email address is not verified.\n"
            "Unable to send maintenance request email.\n"
            "Please verify your email address and try again."
        )
        expected_logged_error = (
            "User bob has not verified their email address. "
            "Unable to send maintenance request email."
        )

        _check_creating_a_job_flashes_and_logs_errors(
            bob_agent_user_without_verified_email_client,
            caplog,
            expected_flashed_message,
            expected_logged_error,
        )

    def test_error_flash_when_marnie_user_email_address_not_verified(
        self,
        bob_agent_user_client: Client,
        marnie_user_without_verified_email: User,
        caplog: pytest.LogCaptureFixture,
        superuser_user: User,
    ) -> None:
        """Test that agents see an error message when Marnie's email is not verified.

        Args:
            bob_agent_user_client (Client): A test client for Bob, an agent user.
            marnie_user_without_verified_email (User): Marnie's user instance without
                                                       a verified email address.
            caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
            superuser_user (User): A superuser instance used for additional validation.
        """
        expected_flashed_message = (
            "Marnie's email address is not verified.\n"
            "Unable to send maintenance request email.\n"
            "Please contact the system administrator at " + get_sysadmin_email()
        )
        expected_logged_error = (
            "Marnie's email address is not verified. "
            "Unable to send maintenance request email."
        )

        _check_creating_a_job_flashes_and_logs_errors(
            bob_agent_user_client,
            caplog,
            expected_flashed_message,
            expected_logged_error,
        )


def _get_flashed_message_after_creating_a_job(client: Client) -> Message:
    """Get the flashed message after creating a job.

    Args:
        client (Client): A test client used to create a job.

    Returns:
        Message: The flashed message displayed after creating a job.
    """
    response = client.post(
        reverse("jobs:job_create"),
        {
            "date": "2022-01-01",
            "address_details": "1234 Main St, Springfield, IL",
            "gps_link": "https://www.google.com/maps",
            "quote_request_details": "Replace the kitchen sink",
        },
    )
    assert response.status_code == status.HTTP_302_FOUND
    response = client.get(response.url)  # type: ignore[attr-defined]
    messages = list(response.context["messages"])
    assert len(messages) == 1
    return cast(Message, messages[0])


def _check_creating_a_job_flashes_and_logs_errors(
    client: Client,
    caplog: pytest.LogCaptureFixture,
    expected_flashed_error_message: str,
    expected_logged_error: str,
) -> None:
    """Check that creating a job shows a flash message and logs an error.

    Args:
        client (Client): A test client used to create a job.
        caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
        expected_flashed_error_message (str): The expected flashed error.
        expected_logged_error (str): The expected error message.
    """
    flashed_message = _get_flashed_message_after_creating_a_job(client)
    assert flashed_message.message == expected_flashed_error_message
    assert flashed_message.level_tag == "error"
    _check_one_error_logged_with_message(caplog, expected_logged_error)


def _check_one_error_logged_with_message(
    caplog: pytest.LogCaptureFixture,
    message: str,
) -> None:
    """Check that exactly one error was logged with the specified message.

    Args:
        caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
        message (str): The message to check for in the log.
    """
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert caplog.records[0].message == message


@pytest.mark.django_db()
def test_maintenance_jobs_page_returns_correct_html(
    bob_agent_user_client: Client,
) -> None:
    """Verify the maintenance jobs page loads with the correct HTML.

    Args:
        bob_agent_user_client (Client): A test client for user Bob who is an agent.
    """
    response = check_basic_page_html_structure(
        client=bob_agent_user_client,
        url="/jobs/",
        expected_title="Maintenance Jobs",
        expected_h1_text="Maintenance Jobs",
        expected_template_name="jobs/job_list.html",
        expected_func_name="view",
        expected_url_name="job_list",
        expected_view_class=JobListView,
    )

    # Parse HTML so that we can check for specific elements
    response_text = response.content.decode()
    soup = BeautifulSoup(response_text, "html.parser")

    # Grab the table element
    table = soup.find("table")
    assert table, "Table element should exist in the HTML"

    # Check the table headers
    headers = table.find_all("th")
    assert headers, "Table headers should exist in the HTML"
    assert [header.get_text(strip=True) for header in headers] == [
        "Number",
        "Date",
        "Address Details",
        "GPS Link",
        "Quote Request Details",
    ]


@pytest.mark.django_db()
def test_create_maintenance_job_page_returns_correct_html(
    bob_agent_user_client: Client,
) -> None:
    """Ensure the create maintenance job page returns the expected HTML content.

    Args:
        bob_agent_user_client (Client): A test client for user Bob who is an agent.
    """
    check_basic_page_html_structure(
        client=bob_agent_user_client,
        url="/jobs/create/",
        expected_title="Create Maintenance Job",
        expected_h1_text="Create Maintenance Job",
        expected_template_name="jobs/job_create.html",
        expected_func_name="view",
        expected_url_name="job_create",
        expected_view_class=JobCreateView,
    )


def test_creating_a_job_sets_status_to_pending_inspection(
    bob_agent_user_client: Client,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """Creating a job should automatically set the status to `pending inspection`.

    Args:
        bob_agent_user_client (Client): Client used by Bob, an agent user.
        bob_agent_user (User): Bob's user instance, an agent.
        marnie_user (User): Marnie's user instance, used for validation in this test.
    """
    client = bob_agent_user_client
    response = client.post(
        reverse("jobs:job_create"),
        {
            "date": "2022-01-01",
            "address_details": "1234 Main St, Springfield, IL",
            "gps_link": "https://www.google.com/maps",
            "quote_request_details": "Replace the kitchen sink",
        },
    )
    assert response.status_code == status.HTTP_302_FOUND
    job = Job.objects.first()
    assert job is not None

    assert job.status == Job.Status.PENDING_INSPECTION.value
