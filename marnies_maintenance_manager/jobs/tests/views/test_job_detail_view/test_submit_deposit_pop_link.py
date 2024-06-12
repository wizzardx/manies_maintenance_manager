"""Tests for "submit deposit proof of payment" link visibility in the job detail view.

This module contains tests to ensure that the "submit deposit proof of payment" link is
visible to the correct users in the job detail view.
"""

from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job


def _get_submit_deposit_pop_link_or_none(
    job: Job,
    bob_agent_user_client: Client,
) -> BeautifulSoup | None:
    """Get the "submit deposit proof of payment" link, or None if it couldn't be found.

    Args:
        job (Job): The job to get the "submit deposit proof of payment" link for.
        bob_agent_user_client (Client): The Django test client for Bob.

    Returns:
        BeautifulSoup | None: The "submit deposit proof of payment" link, or None if it
            couldn't be found.
    """
    response = bob_agent_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the link
    # to submit the deposit proof of payment.
    soup = BeautifulSoup(page, "html.parser")
    return soup.find("a", string="Submit Deposit Proof of Payment")


class TestSubmitDepositPOPLinkVisibility:
    """Ensure correct visibility of the "submit deposit proof of payment" link."""

    @staticmethod
    def test_agent_who_created_job_can_see_submit_deposit_pop_link_when_quote_accepted(
        job_accepted_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure Bob can see "submit deposit proof of payment" link if quote accepted.

        Args:
            job_accepted_by_bob (Job): The job created by Bob with the quote accepted by
                the agent.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        link = _get_submit_deposit_pop_link_or_none(
            job_accepted_by_bob,
            bob_agent_user_client,
        )
        assert link is not None

    @staticmethod
    def test_page_with_link_not_accessible_to_agents_who_did_not_create_job(
        job_accepted_by_bob: Job,
        alice_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't access the detail page.

        Args:
            job_accepted_by_bob (Job): The job created by Bob with the quote accepted by
                the agent.
            alice_agent_user_client (Client): The Django test client for Alice.
        """
        response = alice_agent_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_accepted_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_link_not_visible_when_quote_not_accepted(
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure "submit deposit proof of payment" link is hidden if quote unaccepted.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        link = _get_submit_deposit_pop_link_or_none(
            job_created_by_bob,
            bob_agent_user_client,
        )
        assert link is None

    @staticmethod
    def test_link_not_visible_to_marnie(
        job_accepted_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure Marnie cannot see the "submit deposit proof of payment" link.

        Args:
            job_accepted_by_bob (Job): The job created by Bob with the quote accepted by
                the agent.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        link = _get_submit_deposit_pop_link_or_none(
            job_accepted_by_bob,
            marnie_user_client,
        )
        assert link is None

    @staticmethod
    def test_link_visible_to_admin(
        job_accepted_by_bob: Job,
        admin_client: Client,
    ) -> None:
        """Ensure the admin user can see the "submit deposit proof of payment" link.

        Args:
            job_accepted_by_bob (Job): The job created by Bob with the quote accepted by
                the agent.
            admin_client (Client): The Django test client for the admin user.
        """
        link = _get_submit_deposit_pop_link_or_none(
            job_accepted_by_bob,
            admin_client,
        )
        assert link is not None
