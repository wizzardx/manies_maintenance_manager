"""Tests for the job "complete inspection" view."""

# pylint: disable=redefined-outer-name,unused-argument,magic-value-comparison

import datetime
import logging
from collections.abc import Iterator

import pytest
import pytest_mock
from django.contrib.messages.storage.base import Message
from django.core import mail
from django.template.response import TemplateResponse
from django.test import Client
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.utils import (
    suppress_fastdev_strict_if_deprecation_warning,
)
from marnies_maintenance_manager.jobs.views.job_complete_inspection import (
    JobCompleteInspectionView,
)
from marnies_maintenance_manager.users.models import User

from .utils import check_basic_page_html_structure
from .utils import post_update_request_and_check_errors


def test_anonymous_user_cannot_access_the_view(
    client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that the anonymous user cannot access the "complete inspection" view.

    Args:
        client (Client): The Django test client.
        bob_job_complete_inspection_url (str): The URL for Bob's jobs
            "complete inspection" view.
    """
    with suppress_fastdev_strict_if_deprecation_warning():
        response = client.get(bob_job_complete_inspection_url, follow=True)

    # This should be a redirect to a login page:
    assert response.status_code == status.HTTP_200_OK

    expected_redirect_chain = [
        (
            "/accounts/login/?next=/jobs/"
            f"{bob_job_complete_inspection_url.split('/')[-3]}/complete_inspection/",
            status.HTTP_302_FOUND,
        ),
    ]
    assert response.redirect_chain == expected_redirect_chain


def test_agent_user_cannot_access_the_view(
    bob_agent_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that the agent user cannot access the "complete inspection" view.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_complete_inspection_url (str): The URL for Bob's jobs
            "complete inspection" view.
    """
    response = bob_agent_user_client.get(bob_job_complete_inspection_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_user_can_access_the_view(
    superuser_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that the admin user can access the "complete inspection" view.

    Args:
        superuser_client (Client): The Django test client for the superuser.
        bob_job_complete_inspection_url (str): The URL for Bob's jobs
            "complete inspection" view.
    """
    response = superuser_client.get(bob_job_complete_inspection_url)
    assert response.status_code == status.HTTP_200_OK


def test_marnie_user_can_access_the_view(
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that the Marnie user can access the "complete inspection" view.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for Bob's jobs
            "complete inspection" view.
    """
    response = marnie_user_client.get(bob_job_complete_inspection_url)
    assert response.status_code == status.HTTP_200_OK


def test_page_has_basic_correct_structure(
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that the jobs "complete inspection" page has the correct basic structure.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for Bob's jobs
            "complete inspection" view.
    """
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=bob_job_complete_inspection_url,
        expected_title="Complete Inspection",
        expected_template_name="jobs/job_complete_inspection.html",
        expected_h1_text="Complete Inspection",
        expected_func_name="view",
        expected_url_name="job_complete_inspection",
        expected_view_class=JobCompleteInspectionView,
    )


def test_view_has_date_of_inspection_field(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that the jobs "complete inspection" page has the 'date_of_inspection' field.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for Bob's jobs
            "complete inspection" view.
    """
    post_job_update_and_check_response(
        marnie_user_client,
        bob_job_complete_inspection_url,
        job_created_by_bob,
    )

    assert job_created_by_bob.date_of_inspection == datetime.date(2001, 2, 5)


def post_job_update_and_check_response(
    marnie_user_client: Client,
    bob_job_update_url: str,
    job_created_by_bob: Job,
) -> None:
    """Send "complete inspection" POST request and check the response.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bob's "complete inspection" view.
        job_created_by_bob (Job): The job created by Bob.
    """
    response = marnie_user_client.post(
        bob_job_update_url,
        {
            "date_of_inspection": "2001-02-05",
        },
        follow=True,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        ("/jobs/?agent=bob", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database:
    job_created_by_bob.refresh_from_db()


def test_date_of_inspection_field_is_required(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that the 'date_of_inspection' field is required.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for the
            "complete inspection" view
    """
    post_update_request_and_check_errors(
        client=marnie_user_client,
        url=bob_job_complete_inspection_url,
        data={},
        field_name="date_of_inspection",
        expected_error="This field is required.",
    )


def test_updating_job_changes_status_to_inspection_completed(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that updating the job changes the status to 'Inspection Completed'.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for the "complete inspection"
            view
    """
    # POST request to upload new details:
    post_job_update_and_check_response(
        marnie_user_client,
        bob_job_complete_inspection_url,
        job_created_by_bob,
    )

    # Check that the status changed as expected
    assert job_created_by_bob.status == Job.Status.INSPECTION_COMPLETED.value


def test_marnie_cannot_access_view_after_initial_site_inspection(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Ensure Marnie can't access the update view after completing initial inspection.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for the "complete job" view
            for the job created by Bob.
    """
    response = marnie_user_client.get(bob_job_complete_inspection_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_superuser_cannot_access_view_after_initial_site_inspection(
    bob_job_with_initial_marnie_inspection: Job,
    superuser_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Ensure the superuser can't access the update view after Marnie already inspected.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        superuser_client (Client): The Django test client for the superuser.
        bob_job_complete_inspection_url (str): The URL for the "complete job" view
            for the job created by Bob.
    """
    response = superuser_client.get(bob_job_complete_inspection_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_clicking_save_redirects_to_job_listing_page(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> None:
    """Test that clicking 'Save' redirects to the job listing page.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for the view where Marnie can
            inspect the site from the job created by Bob.
    """
    post_job_update_and_check_response(
        marnie_user_client,
        bob_job_complete_inspection_url,
        job_created_by_bob,
    )


@pytest.fixture()
def http_response_to_marnie_inspecting_site_of_job_by_bob(
    job_created_by_bob: Job,
    bob_job_complete_inspection_url: str,
    marnie_user_client: Client,
) -> TemplateResponse:
    """Get the HTTP response after Marnie inspects the site of the job created by Bob.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        bob_job_complete_inspection_url (str): The URL for the view where Marnie can
            inspect the site from the job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.

    Returns:
        TemplateResponse: The HTTP response after Marnie inspects the site of the job
    """
    response = check_type(
        marnie_user_client.post(
            bob_job_complete_inspection_url,
            {
                "date_of_inspection": "2001-02-05",
            },
            follow=True,
        ),
        TemplateResponse,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Return the response to the caller
    return response


@pytest.fixture()
def flashed_message_after_inspecting_a_site(
    http_response_to_marnie_inspecting_site_of_job_by_bob: TemplateResponse,
) -> Message:
    """Retrieve the flashed message after Marnie inspects a site.

    Args:
        http_response_to_marnie_inspecting_site_of_job_by_bob (TemplateResponse): The
            HTTP response after Marnie inspects the site.

    Returns:
        Message: The flashed message after Marnie inspects a site.
    """
    # Check the messages:
    response = http_response_to_marnie_inspecting_site_of_job_by_bob
    messages = list(response.context["messages"])
    assert len(messages) == 1

    # Return the retrieved message to the caller
    return check_type(messages[0], Message)


def test_a_flash_message_is_displayed_when_marnie_clicks_save(
    flashed_message_after_inspecting_a_site: Message,
) -> None:
    """Test that a flash message is displayed when Marnie clicks 'Save'.

    Args:
        flashed_message_after_inspecting_a_site (Message): The flashed message after
            Marnie inspects a site.
    """
    # Marnie should see a "Maintenance Update email has been sent to <agent username>"
    # flash message when she clicks the "Save" button.
    flashed_message = flashed_message_after_inspecting_a_site
    assert flashed_message.message == "An email has been sent to bob."
    assert flashed_message.level_tag == "success"


def test_marnie_clicking_save_sends_an_email_to_agent(
    http_response_to_marnie_inspecting_site_of_job_by_bob: TemplateResponse,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """Test that Marnie clicking 'Save' sends an email to the agent.

    Args:
        http_response_to_marnie_inspecting_site_of_job_by_bob (TemplateResponse): The
            HTTP response after Marnie inspects the site.
        bob_agent_user (User): The agent user Bob.
        marnie_user (User): The user Marnie.
    """
    # For the earlier part of our fixtures (job creation by agent), we built the model
    # instance directly, rather than going through the view-based logic, so an email
    # wouldn't have been sent there.

    # But for the most recent part of the fixtures (Marnie inspecting the site and
    # updating thew website), we did go through the view-based logic, so an email
    # should have been sent there.
    num_mails_sent = len(mail.outbox)
    assert num_mails_sent == 1

    # Grab the mail:
    email = mail.outbox[0]

    # Check various details of the mail here.

    # Check mail metadata:
    assert (
        email.subject == "Marnie completed an inspection for your maintenance request"
    )
    assert bob_agent_user.email in email.to
    assert marnie_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Marnie performed the inspection on 2001-02-05. "
        "An email with the quote will be sent later." in email.body
    )


@pytest.fixture()
def log_capture(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture logs for testing.

    Args:
        caplog (pytest.LogCaptureFixture): The log capture fixture.

    Yields:
        Iterator[pytest.LogCaptureFixture]: The log capture fixture.
    """
    with caplog.at_level(
        logging.INFO,
        logger="marnies_maintenance_manager.jobs.views.job_complete_inspection",
    ):
        yield caplog


def test_email_logging_when_skip_email_send_is_true(
    mocker: pytest_mock.MockFixture,
    log_capture: pytest.LogCaptureFixture,
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
    job_created_by_bob: Job,
) -> None:
    """Test that the correct log message is generated when SKIP_EMAIL_SEND is True.

    Args:
        mocker: The mocker fixture for patching.
        log_capture (None): Fixture to capture logs for testing.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for Bob's job
            "complete inspection" view.
        job_created_by_bob (Job): The job created by Bob.
    """
    mocker.patch(
        "marnies_maintenance_manager.jobs.views.job_complete_inspection.SKIP_EMAIL_SEND",
        new=True,
    )

    response = marnie_user_client.post(
        bob_job_complete_inspection_url,
        {
            "date_of_inspection": "2001-02-05",
        },
        follow=True,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        ("/jobs/?agent=bob", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database:
    job_created_by_bob.refresh_from_db()

    # Check that the expected log message is present
    expected_log_message = (
        "Skipping email send. Would have sent the following email:\n\n"
        "Subject: Marnie completed an inspection for your maintenance request\n\n"
        "Body: Marnie performed the inspection on 2001-02-05. An email "
        "with the quote will be sent later.\n\nDetails of your original request:\n\n"
        "-----\n\nSubject: New maintenance request by bob\n\n"
    )
    assert any(
        expected_log_message in record.message for record in log_capture.records
    )  # pragma: no cover
