"""Tests for the accept_quote view."""

# pylint: disable=magic-value-comparison,too-many-arguments

from uuid import UUID

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.http import Http404
from django.http import HttpResponseRedirect
from django.test import Client
from django.test import RequestFactory
from rest_framework import status
from typeguard import check_type

from manies_maintenance_manager.jobs import constants
from manies_maintenance_manager.jobs.exceptions import LogicalError
from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.tests.views.utils import (
    assert_standard_email_content,
)
from manies_maintenance_manager.jobs.tests.views.utils import (
    assert_standard_quote_post_response,
)
from manies_maintenance_manager.jobs.views.quote_accept_view import quote_accept
from manies_maintenance_manager.users.models import User


def test_logging_in_is_required_to_accept_quote() -> None:
    """Test that logging in is required to accept a quote."""
    # Assign job_id to a UUID:
    job_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    # Over here we need to log in using a request factory, but at the same time
    # also signing in as the user referred to by bob_agent_user
    request = RequestFactory().post(f"/jobs/{job_id}/quote/accept/")
    request.user = AnonymousUser()
    # Call the view function:d
    response = check_type(quote_accept(request, job_id), HttpResponseRedirect)
    # Assert that the status code is as expected
    assert response.status_code == status.HTTP_302_FOUND
    # Check that the response redirects to the login page
    expected_url = f"/accounts/login/?next=/jobs/{job_id}/quote/accept/"
    assert response.url == expected_url


def test_only_the_post_method_may_be_used(bob_agent_user: User) -> None:
    """Test that only the POST method may be used.

    Args:
        bob_agent_user (User): The user who is an agent.
    """
    # Arrange
    request = RequestFactory().get(
        "/jobs/123e4567-e89b-12d3-a456-426614174000/accept_quote",
    )
    request.user = bob_agent_user

    # Act
    response = quote_accept(request, UUID("123e4567-e89b-12d3-a456-426614174000"))

    # Assert
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.content.decode() == "Method not allowed"


def test_does_not_work_for_manie(
    manie_user: User,
    bob_job_with_quote: Job,
) -> None:
    """Test that the view does not work for Manie.

    Args:
        manie_user (User): The user who is Manie.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    perform_post_request_and_check_response(
        manie_user,
        bob_job_with_quote,
        status.HTTP_403_FORBIDDEN,
    )


def perform_post_request_and_check_response(
    user: User,
    job: Job,
    expected_status: int,
) -> None:
    """Perform a POST request and check the response.

    Args:
        user (User): The user making the request.
        job (Job): The job instance related to the request.
        expected_status (int): The expected HTTP status code of the response.
    """
    # Arrange
    job_id = job.id
    request = RequestFactory().post(f"/jobs/{job_id}/quote/accept/")
    request.user = user

    # Act
    response = quote_accept(request, job_id)

    # Assert
    assert response.status_code == expected_status


def test_fails_for_nonexistent_job(bob_agent_user: User) -> None:
    """Test that the view fails for a job that does not exist.

    Args:
        bob_agent_user (User): The user who is an agent.
    """
    # Arrange
    request = RequestFactory().post(
        "/jobs/123e4567-e89b-12d3-a456-426614174000/accept_quote",
    )
    request.user = bob_agent_user

    # Act
    with pytest.raises(Http404):
        quote_accept(request, UUID("123e4567-e89b-12d3-a456-426614174000"))

    # Assert - the fact that the view raises a 404 exception is the assertion.


def test_fails_for_jobs_in_incorrect_states(  # noqa: PLR0913
    bob_agent_user: User,
    job_created_by_bob: Job,
    job_accepted_by_bob: Job,
    bob_job_with_deposit_pop: Job,
    bob_job_with_onsite_work_completed_by_manie: Job,
    bob_job_with_manie_final_documentation: Job,
    bob_job_with_final_payment_pop: Job,
    bob_job_with_quote: Job,
) -> None:
    """Test that the view fails for jobs in incorrect states.

    Args:
        bob_agent_user (User): The user who is an agent.
        job_created_by_bob (Job): The job created by Bob.
        job_accepted_by_bob (Job): The job accepted by Bob.
        bob_job_with_deposit_pop (Job): The job with the deposit pop uploaded by Bob.
        bob_job_with_onsite_work_completed_by_manie (Job): The job with the onsite work
            completed by Manie.
        bob_job_with_manie_final_documentation (Job): The job with the final
            documentation uploaded by Manie.
        bob_job_with_final_payment_pop (Job): The job with the final payment pop
            uploaded
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.

    Raises:
        LogicalError: If an unknown state is encountered.
    """
    # The allowed states are INSPECTION_COMPLETED and QUOTE_REJECTED_BY_AGENT.
    # In this test, we loop through all the known states, except for the above.
    for state in Job.Status:
        if state in {
            Job.Status.INSPECTION_COMPLETED,
            Job.Status.QUOTE_REJECTED_BY_AGENT,
        }:
            continue
        # Depending on the state, we prepare a different testing job:
        match state:
            case Job.Status.PENDING_INSPECTION:
                job = job_created_by_bob
            case Job.Status.QUOTE_UPLOADED:
                job = bob_job_with_quote
            case Job.Status.QUOTE_ACCEPTED_BY_AGENT:
                job = job_accepted_by_bob
            case Job.Status.DEPOSIT_POP_UPLOADED:
                job = bob_job_with_deposit_pop
            case Job.Status.MANIE_COMPLETED_ONSITE_WORK:
                job = bob_job_with_onsite_work_completed_by_manie
            case Job.Status.MANIE_SUBMITTED_DOCUMENTATION:
                job = bob_job_with_manie_final_documentation
            case Job.Status.FINAL_PAYMENT_POP_UPLOADED:
                job = bob_job_with_final_payment_pop
            case _:  # pragma: no cover
                # This logic should never be reached, as we are looping through all the
                # known states.
                msg = f"Unknown state {state}"
                raise LogicalError(msg)

        # Arrange:
        request = RequestFactory().post(f"/jobs/{job.id}/quote/accept/")
        request.user = bob_agent_user

        # Act:
        response = quote_accept(request, job.id)

        # Assert:
        assert response.status_code == status.HTTP_412_PRECONDITION_FAILED
        assert (
            response.content.decode()
            == "Job is not in the correct state for accepting a quote."
        )


def test_does_not_work_for_agent_who_did_not_create_the_job(
    alice_agent_user: User,
    bob_job_with_quote: Job,
) -> None:
    """Test that the view does not work for an agent who did not create the job.

    Args:
        alice_agent_user (User): The user who is an agent.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote
    """
    perform_post_request_and_check_response(
        alice_agent_user,
        bob_job_with_quote,
        status.HTTP_403_FORBIDDEN,
    )


def assert_quote_accept_redirects_to_job_details(client: Client, job: Job) -> None:
    """Assert that accepting a quote redirects to the job details page.

    Args:
        client (Client): The Django test client.
        job (Job): The job instance.
    """
    job_id = job.id
    response = check_type(
        client.post(
            f"/jobs/{job_id}/quote/accept/",
        ),
        HttpResponseRedirect,
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == f"/jobs/{job_id}/"


def test_redirects_to_job_details_page(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Test that the view redirects to the job details page.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    assert_quote_accept_redirects_to_job_details(
        bob_agent_user_client,
        bob_job_with_quote,
    )


def test_works_for_admin(
    admin_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Test that the view works for an admin.

    Args:
        admin_client (Client): The Django test client for the admin user.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    assert_quote_accept_redirects_to_job_details(
        admin_client,
        bob_job_with_quote,
    )


def test_works_when_manie_just_inspected_and_created_a_quote(
    bob_job_with_quote: Job,
    bob_agent_user_client: Client,
) -> None:
    """Test that the view works when Manie just inspected and created a quote.

    Args:
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    assert_quote_accept_redirects_to_job_details(
        bob_agent_user_client,
        bob_job_with_quote,
    )


def test_when_agent_has_rejected_manies_quote(
    job_rejected_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Test that the view works when the agent has rejected Manie's quote.

    Args:
        job_rejected_by_bob (Job): The job rejected by Bob.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    assert_quote_accept_redirects_to_job_details(
        bob_agent_user_client,
        job_rejected_by_bob,
    )


def test_sets_job_status_to_quote_accepted(
    job_rejected_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Test that the view sets the job status to 'quote accepted'.

    Args:
        job_rejected_by_bob (Job): The job rejected by Bob.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = job_rejected_by_bob
    response = check_type(
        bob_agent_user_client.post(
            f"/jobs/{job.id}/quote/accept/",
        ),
        HttpResponseRedirect,
    )

    assert response.status_code == status.HTTP_302_FOUND
    job.refresh_from_db()
    assert job.status == Job.Status.QUOTE_ACCEPTED_BY_AGENT.value
    assert job.accepted_or_rejected == Job.AcceptedOrRejected.ACCEPTED.value


def test_sends_email_to_manie(
    bob_agent_user: User,
    job_rejected_by_bob: Job,
    manie_user: User,
    bob_agent_user_client: Client,
) -> None:
    """Test that the view sends an email to Manie.

    Args:
        bob_agent_user (User): The user who is an agent.
        job_rejected_by_bob (Job): The job rejected by Bob.
        manie_user (User): The user who is Manie.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job_id = job_rejected_by_bob.id
    mail.outbox.clear()
    response = check_type(
        bob_agent_user_client.post(
            f"/jobs/{job_id}/quote/accept/",
        ),
        HttpResponseRedirect,
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == f"/jobs/{job_id}/"

    # Check that an email was sent, with the expected details.
    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check mail metadata:
    assert email.subject == "Quote accepted by bob"
    assert manie_user.email in email.to
    assert bob_agent_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert "Agent bob has accepted the quote for a maintenance job." in email.body

    # Check the rest of the email contents:
    assert_standard_email_content(email, job_rejected_by_bob)


def test_creates_a_flash_message(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Test that the view creates a flash message.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    messages = assert_standard_quote_post_response(
        bob_agent_user_client,
        bob_job_with_quote,
        "accept",
    )
    assert str(messages[0]) == "Quote accepted. An email has been sent to Manie."
