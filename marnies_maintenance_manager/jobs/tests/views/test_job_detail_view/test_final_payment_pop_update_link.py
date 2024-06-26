"""Tests for "Upload Final Payment POP" link visibility in job detail views.

This module contains a series of tests to verify the visibility and accessibility of the
"Upload Final Payment POP" link on the job detail page within the Marnie's Maintenance
Manager application, based on different user roles and job completion status.

Utilizing Django's test client and BeautifulSoup for HTML parsing, these tests ensure:
- Only agents who created the job can see the link if the job is completed.
- Agents not involved in the job creation cannot access the page at all.
- The link is not visible when the job is not completed, regardless of the user.
- Specific roles like Marnie do not have access to this link, whereas admin users do.

Functions:
    _get_final_payment_pop_update_link_or_none: Fetches the link for updating final
        payment POP if present.
    test_agent_who_created_job_can_see_link: Verifies link visibility for the job
        creator.
    test_test_page_with_link_not_accessible_to_agents_who_did_not_create_job: Ensures
        access restrictions.
    test_link_not_visible_when_job_not_completed: Checks link visibility based on job
        status.
    test_link_not_visible_to_marnie: Asserts role-based link visibility.
    test_link_is_visible_to_admin: Confirms admin access to the link.

Each function assesses different conditions of access and visibility, using assertions
to evaluate the presence or absence of the link and HTTP status codes to validate page
accessibility.

"""

from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job


def _get_final_payment_pop_update_link_or_none(
    job: Job,
    client: Client,
) -> BeautifulSoup | None:
    response = client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the link
    # to submit the deposit proof of payment.
    soup = BeautifulSoup(page, "html.parser")
    return soup.find("a", string="Upload Final Payment POP")


def test_agent_who_created_job_can_see_link(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the agent who created the job can see the "submit final payment POP" link.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    link = _get_final_payment_pop_update_link_or_none(
        bob_job_completed_by_marnie,
        bob_agent_user_client,
    )
    assert link is not None


def test_test_page_with_link_not_accessible_to_agents_who_did_not_create_job(
    bob_job_completed_by_marnie: Job,
    alice_agent_user_client: Client,
) -> None:
    """Ensure page with link is not accessible to agents who did not create the job.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        alice_agent_user_client (Client): The Django test client for Alice. She did not
            create the job.
    """
    response = alice_agent_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": bob_job_completed_by_marnie.pk}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_link_not_visible_when_job_not_completed(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the link is not visible when the job is not completed.

    Args:
        job_accepted_by_bob (Job): The job created by Bob, with a quote added by Marnie
            that was also accepted by Bob, but not marked as complete.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    link = _get_final_payment_pop_update_link_or_none(
        job_accepted_by_bob,
        bob_agent_user_client,
    )
    assert link is None


def test_link_not_visible_to_marnie(
    bob_job_completed_by_marnie: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure the link is not visible to Marnie.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    link = _get_final_payment_pop_update_link_or_none(
        bob_job_completed_by_marnie,
        marnie_user_client,
    )
    assert link is None


def test_link_is_visible_to_admin(
    bob_job_completed_by_marnie: Job,
    admin_client: Client,
) -> None:
    """Ensure the link is visible to an admin user.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        admin_client (Client): The Django test client for an admin user.
    """
    link = _get_final_payment_pop_update_link_or_none(
        bob_job_completed_by_marnie,
        admin_client,
    )
    assert link is not None
