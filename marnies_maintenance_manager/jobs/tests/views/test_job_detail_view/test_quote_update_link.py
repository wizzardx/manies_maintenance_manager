"""Tests for the visibility of the quote download link in the job detail view.

This module contains tests to ensure that the quote download link is visible to
the correct users in the job detail view.
"""

from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    _get_page_soup,
)


def _get_update_quote_link_or_none(
    job: Job,
    user_client: Client,
) -> BeautifulSoup | None:
    """Get the update quote link, or None if it couldn't be found.

    Args:
        job (Job): The job to get the update quote link for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The update quote link, or None if it couldn't be found.
    """
    soup = _get_page_soup(job, user_client)
    return soup.find("a", string="Upload new Quote")


class TestUpdateQuoteLinkVisibility:
    """Tests to ensure that the update quote link is visible to the correct users."""

    @staticmethod
    def test_marnie_can_see_update_quote_link_after_agent_rejected_initial_quote(
        job_rejected_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure Marnie sees the update quote link after the agent rejects it.

        Args:
            job_rejected_by_bob (Job): The job created by Bob with the quote rejected by
                the agent.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        link = _get_update_quote_link_or_none(job_rejected_by_bob, marnie_user_client)
        assert link is not None

    @staticmethod
    def test_is_not_present_for_jobs_in_other_states(
        job_created_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure the update quote link is not present for jobs in other states.

        Args:
            job_created_by_bob (Job): The newly created job created by Bob.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        link = _get_update_quote_link_or_none(job_created_by_bob, marnie_user_client)
        assert link is None

    @staticmethod
    def test_is_not_present_for_agents(
        job_rejected_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the update quote link is not present for agents.

        Args:
            job_rejected_by_bob (Job): The job created by Bob with the quote rejected by
                the agent.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        link = _get_update_quote_link_or_none(
            job_rejected_by_bob,
            bob_agent_user_client,
        )
        assert link is None

    @staticmethod
    def test_is_visible_for_admins(
        job_rejected_by_bob: Job,
        admin_client: Client,
    ) -> None:
        """Ensure the update quote link is visible for admins.

        Args:
            job_rejected_by_bob (Job): The job created by Bob with the quote rejected by
                the agent.
            admin_client (Client): The Django test client for the admin user.
        """
        link = _get_update_quote_link_or_none(job_rejected_by_bob, admin_client)
        assert link is not None

    @staticmethod
    def test_link_points_to_quote_update_url(
        job_rejected_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure the update quote link points to the correct URL.

        Args:
            job_rejected_by_bob (Job): The job created by Bob with the quote rejected by
                the agent.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        link = _get_update_quote_link_or_none(job_rejected_by_bob, marnie_user_client)
        assert link is not None

        # Confirm that the link goes to the correct URL.
        expected_url = reverse(
            "jobs:quote_update",
            kwargs={"pk": job_rejected_by_bob.pk},
        )
        assert link["href"] == expected_url
