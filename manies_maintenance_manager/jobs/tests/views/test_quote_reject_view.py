"""Tests for the reject quote view."""

# pylint: disable=magic-value-comparison

import pytest
from django.core import mail
from django.http import HttpResponseRedirect
from django.test import Client
from rest_framework import status
from typeguard import check_type

from manies_maintenance_manager.jobs import constants
from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.tests.utils import (
    suppress_fastdev_strict_if_deprecation_warning,
)
from manies_maintenance_manager.jobs.tests.views.utils import (
    assert_standard_email_content,
)
from manies_maintenance_manager.jobs.tests.views.utils import (
    assert_standard_quote_post_response,
)
from manies_maintenance_manager.users.models import User


@pytest.mark.django_db()
def test_gets_redirected_to_login_for_anonymous_user(client: Client) -> None:
    """Ensure that an anonymous user is redirected to the login page.

    Args:
        client (Client): The Django test client.
    """
    with suppress_fastdev_strict_if_deprecation_warning():
        response = client.get(
            "/jobs/0dd3c34c-2003-11ef-8db1-5baa8ebc9c58/quote/reject/",
            follow=True,
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.redirect_chain == [
        (
            "/accounts/login/?next=/jobs/0dd3c34c-2003-11ef-8db1-5baa8ebc9c58/quote/reject/",
            302,
        ),
    ]


def test_fails_for_none_post_request(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure that the view fails for a GET request.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    response = bob_agent_user_client.get(
        f"/jobs/{bob_job_with_quote.id}/quote/reject/",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_gets_permission_error_for_manie_user(
    manie_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure that Manie cannot reject the quote for Bob's job.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    response = manie_user_client.post(
        f"/jobs/{bob_job_with_quote.id}/quote/reject/",
        follow=True,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_gets_permission_error_for_different_agent_user(
    alice_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure that Alice cannot reject the quote for Bob's job.

    Args:
        alice_agent_user_client (Client): The Django test client for Alice.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    response = alice_agent_user_client.post(
        f"/jobs/{bob_job_with_quote.id}/quote/reject/",
        follow=True,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fails_if_job_not_in_correct_state(
    bob_agent_user_client: Client,
    job_created_by_bob: Job,
) -> None:
    """Ensure that Bob cannot reject the quote if the job is not in the correct state.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        job_created_by_bob (Job): The job created by Bob.
    """
    response = bob_agent_user_client.post(
        f"/jobs/{job_created_by_bob.id}/quote/reject/",
    )
    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED
    assert (
        response.content.decode("utf-8")
    ).strip() == "Job is not in the correct state for rejecting a quote."


def test_can_reject_when_job_already_in_rejected_state(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure Bob can reject the quote when the job is already in the REJECTED state.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    bob_job_with_quote.status = Job.Status.QUOTE_REJECTED_BY_AGENT.value
    bob_job_with_quote.save()
    response = bob_agent_user_client.post(
        f"/jobs/{bob_job_with_quote.id}/quote/reject/",
    )
    assert response.status_code == status.HTTP_302_FOUND
    response2 = check_type(response, HttpResponseRedirect)
    assert response2.url == f"/jobs/{bob_job_with_quote.id}/"


def test_fails_for_nonexistent_job(bob_agent_user_client: Client) -> None:
    """Ensure that the view fails for a nonexistent job.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.post(
        "/jobs/0dd3c34c-2003-11ef-8db1-5baa8ebc9c58/quote/reject/",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_redirects_to_job_detail_view(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure user is redirected to the job detail view after rejecting the quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    response = bob_agent_user_client.post(
        f"/jobs/{bob_job_with_quote.id}/quote/reject/",
    )
    assert response.status_code == status.HTTP_302_FOUND
    response2 = check_type(response, HttpResponseRedirect)
    assert response2.url == f"/jobs/{bob_job_with_quote.id}/"


def test_sets_job_to_rejected_by_agent(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure that the job is set to REJECTED_BY_AGENT after rejecting the quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    job = _reject_quote_and_get_job(
        bob_agent_user_client,
        bob_job_with_quote,
    )
    assert job.accepted_or_rejected == Job.AcceptedOrRejected.REJECTED.value


def _reject_quote_and_get_job(client: Client, job: Job) -> Job:
    response = client.post(
        f"/jobs/{job.id}/quote/reject/",
    )
    assert response.status_code == status.HTTP_302_FOUND
    response2 = check_type(response, HttpResponseRedirect)
    assert response2.url == f"/jobs/{job.id}/"

    job.refresh_from_db()
    assert job.status == Job.Status.QUOTE_REJECTED_BY_AGENT.value
    return job


def _reject_quote(client: Client, job: Job) -> None:
    """Wrap the _reject_quote_and_get_job() function, discarding the return value.

    Args:
        client (Client): The Django test client.
        job (Job): The job to reject the quote for.
    """
    _reject_quote_and_get_job(client, job)


def test_email_sent_to_manie_user(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure that an email is sent to Manie after Bob rejects the quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
        manie_user (User): The Manie user.
        bob_agent_user (User): The Bob user.
    """
    # Clear out the mailbox before we start:
    mail.outbox.clear()

    # Reject the quote:
    _reject_quote(bob_agent_user_client, bob_job_with_quote)

    # Check that an email was sent, with the expected details.
    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check mail metadata:
    assert email.subject == "Quote rejected by bob"
    assert manie_user.email in email.to
    assert bob_agent_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert "Agent bob has rejected the quote for a maintenance job." in email.body

    # Check the rest of the email contents:
    assert_standard_email_content(email, bob_job_with_quote)


def test_flash_message_displayed(
    bob_agent_user_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure that a flash message is displayed after rejecting a quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    messages = assert_standard_quote_post_response(
        bob_agent_user_client,
        bob_job_with_quote,
        "reject",
    )
    assert str(messages[0]) == "Quote rejected. An email has been sent to Manie."


def test_admin_user_can_reject_quote(
    admin_client: Client,
    bob_job_with_quote: Job,
) -> None:
    """Ensure that the admin user can reject the quote.

    Args:
        admin_client (Client): The Django test client for the admin user.
        bob_job_with_quote (Job): Job where Manie has uploaded a quote.
    """
    _reject_quote(admin_client, bob_job_with_quote)
