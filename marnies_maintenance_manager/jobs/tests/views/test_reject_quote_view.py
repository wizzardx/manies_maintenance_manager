"""Tests for the reject quote view."""

# pylint: disable=magic-value-comparison

from typing import cast

import pytest
from django.core import mail
from django.http import HttpResponseRedirect
from django.test import Client
from rest_framework import status

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User


@pytest.mark.django_db()
def test_gets_redirected_to_login_for_anonymous_user(client: Client) -> None:
    """Ensure that an anonymous user is redirected to the login page.

    Args:
        client (Client): The Django test client.
    """
    # Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    # {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    # while handling a GET request to the /accounts/login/ URL. We can ignore this
    # for our testing.
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        response = client.get(
            "/jobs/0dd3c34c-2003-11ef-8db1-5baa8ebc9c58/reject-quote/",
            follow=True,
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.redirect_chain == [
        (
            "/accounts/login/?next=/jobs/0dd3c34c-2003-11ef-8db1-5baa8ebc9c58/reject-quote/",
            302,
        ),
    ]


def test_fails_for_none_post_request(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure that the view fails for a GET request.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = bob_agent_user_client.get(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/reject-quote/",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_gets_permission_error_for_marnie_user(
    marnie_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure that Marnie cannot reject the quote for Bob's job.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = marnie_user_client.post(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/reject-quote/",
        follow=True,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_gets_permission_error_for_different_agent_user(
    peter_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure that Peter cannot reject the quote for Bob's job.

    Args:
        peter_agent_user_client (Client): The Django test client for Peter.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = peter_agent_user_client.post(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/reject-quote/",
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
        f"/jobs/{job_created_by_bob.id}/reject-quote/",
    )
    assert response.status_code == status.HTTP_412_PRECONDITION_FAILED
    assert response.json() == {
        "error": "Job is not in the correct state for rejecting a quote.",
    }


def test_can_reject_when_job_already_in_rejected_state(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure Bob can reject the quote when the job is already in the REJECTED state.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    bob_job_with_initial_marnie_inspection.status = (
        Job.Status.QUOTE_REJECTED_BY_AGENT.value
    )
    bob_job_with_initial_marnie_inspection.save()
    response = bob_agent_user_client.post(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/reject-quote/",
    )
    assert response.status_code == status.HTTP_302_FOUND
    response2 = cast(HttpResponseRedirect, response)
    assert response2.url == f"/jobs/{bob_job_with_initial_marnie_inspection.id}/"


def test_fails_for_nonexistent_job(bob_agent_user_client: Client) -> None:
    """Ensure that the view fails for a nonexistent job.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.post(
        "/jobs/0dd3c34c-2003-11ef-8db1-5baa8ebc9c58/reject-quote/",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_redirects_to_job_detail_view(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure user is redirected to the job detail view after rejecting the quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = bob_agent_user_client.post(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/reject-quote/",
    )
    assert response.status_code == status.HTTP_302_FOUND
    response2 = cast(HttpResponseRedirect, response)
    assert response2.url == f"/jobs/{bob_job_with_initial_marnie_inspection.id}/"


def test_sets_job_to_rejected_by_agent(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure that the job is set to REJECTED_BY_AGENT after rejecting the quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    job = _reject_quote_and_get_job(
        bob_agent_user_client,
        bob_job_with_initial_marnie_inspection,
    )
    assert job.accepted_or_rejected == Job.AcceptedOrRejected.REJECTED.value


def _reject_quote_and_get_job(client: Client, job: Job) -> Job:
    response = client.post(
        f"/jobs/{job.id}/reject-quote/",
    )
    assert response.status_code == status.HTTP_302_FOUND
    response2 = cast(HttpResponseRedirect, response)
    assert response2.url == f"/jobs/{job.id}/"

    job = Job.objects.get(id=job.id)
    assert job.status == Job.Status.QUOTE_REJECTED_BY_AGENT.value
    return job


def _reject_quote(client: Client, job: Job) -> None:
    """Wrap the _reject_quote_and_get_job() function, discarding the return value.

    Args:
        client (Client): The Django test client.
        job (Job): The job to reject the quote for.
    """
    _reject_quote_and_get_job(client, job)


def test_email_sent_to_marnie_user(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure that an email is sent to Marnie after Bob rejects the quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
        marnie_user (User): The Marnie user.
        bob_agent_user (User): The Bob user.
    """
    # Clear out the mailbox before we start:
    mail.outbox.clear()

    # Reject the quote:
    _reject_quote(bob_agent_user_client, bob_job_with_initial_marnie_inspection)

    # Check that an email was sent, with the expected details.
    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check mail metadata:
    assert email.subject == "Quote rejected by bob"
    assert marnie_user.email in email.to
    assert bob_agent_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Agent bob has rejected the quote for your maintenance request." in email.body
    )

    assert "Details of the original request:" in email.body

    # A separator line:
    assert "-----" in email.body

    # Subject and body of mail that we sent a bit previously:

    assert "Subject: Quote for your maintenance request" in email.body

    assert (
        "Marnie performed the inspection on 2001-02-05 and has quoted you."
        in email.body
    )

    # The original mail subject line, as a line in the body:
    assert "Subject: New maintenance request by bob" in email.body

    # And all the original body lines, too, as per our previous test where the
    # agent user had just created a new job:

    assert "bob has made a new maintenance request." in email.body
    assert "Date: 2022-01-01" in email.body
    assert "Address Details:\n\n1234 Main St, Springfield, IL" in email.body
    assert "GPS Link:\n\nhttps://www.google.com/maps" in email.body
    assert "Quote Request Details:\n\nReplace the kitchen sink" in email.body
    assert (
        "PS: This mail is sent from an unmonitored email address. "
        "Please do not reply to this email." in email.body
    )


def test_flash_message_displayed(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure that a flash message is displayed after rejecting a quote.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = bob_agent_user_client.post(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/reject-quote/",
        follow=True,
    )

    # Check the response code:
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain:
    assert response.redirect_chain == [
        (f"/jobs/{bob_job_with_initial_marnie_inspection.id}/", 302),
    ]

    # Check the message:
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert str(messages[0]) == "Quote rejected. An email has been sent to Marnie."


def test_admin_user_can_reject_quote(
    admin_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure that the admin user can reject the quote.

    Args:
        admin_client (Client): The Django test client for the admin user.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    _reject_quote(admin_client, bob_job_with_initial_marnie_inspection)
