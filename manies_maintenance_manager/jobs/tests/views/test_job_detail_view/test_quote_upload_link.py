"""Tests for the visibility of the "Upload QUote" link in the job detail view.

This module contains tests to ensure that the "Upload Quote" link is visible to
the correct users in the Job Detail view.
"""

from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    _get_page_soup,
)


def _get_upload_quote_link_or_none(
    job: Job,
    user_client: Client,
) -> BeautifulSoup | None:
    """Get the upload quote link, or None if it couldn't be found.

    Args:
        job (Job): The job to get the update quote link for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The Upload Quote link, or None if it couldn't be found.
    """
    soup = _get_page_soup(job, user_client)
    return soup.find("a", string="Upload Quote")


class TestUploadQuoteLinkVisibility:
    """Tests to ensure that the upload quote link is visible to the correct users."""

    @staticmethod
    def test_manie_can_see_upload_quote_link_after_agent_rejected_initial_quote(
        job_rejected_by_bob: Job,
        manie_user_client: Client,
    ) -> None:
        """Ensure Manie sees the upload quote link after he completes the inspection.

        Args:
            job_rejected_by_bob (Job): The job where Bob rejected the attached quote.
            manie_user_client (Client): The Django test client for Manie.
        """
        link = _get_upload_quote_link_or_none(job_rejected_by_bob, manie_user_client)
        assert link is not None

    @staticmethod
    def test_is_not_present_for_jobs_in_other_states(
        job_created_by_bob: Job,
        manie_user_client: Client,
    ) -> None:
        """Ensure the update quote link is not present for jobs in other states.

        Args:
            job_created_by_bob (Job): The newly created job created by Bob.
            manie_user_client (Client): The Django test client for Manie.
        """
        link = _get_upload_quote_link_or_none(job_created_by_bob, manie_user_client)
        assert link is None

    @staticmethod
    def test_is_not_present_for_agents(
        bob_job_with_initial_manie_inspection: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the update quote link is not present for agents.

        Args:
            bob_job_with_initial_manie_inspection (Job): The job created by Bob with
                the initial inspection done by Manie.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        link = _get_upload_quote_link_or_none(
            bob_job_with_initial_manie_inspection,
            bob_agent_user_client,
        )
        assert link is None

    @staticmethod
    def test_is_visible_for_admins(
        bob_job_with_initial_manie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure the upload quote link is visible for admins.

        Args:
            bob_job_with_initial_manie_inspection (Job): The job created by Bob with
                the initial inspection done by Manie.
            admin_client (Client): The Django test client for the admin user.
        """
        link = _get_upload_quote_link_or_none(
            bob_job_with_initial_manie_inspection,
            admin_client,
        )
        assert link is not None

    @staticmethod
    def test_link_points_to_quote_upload_url(
        bob_job_with_initial_manie_inspection: Job,
        manie_user_client: Client,
    ) -> None:
        """Ensure the update quote link points to the correct URL.

        Args:
            bob_job_with_initial_manie_inspection (Job): The job created by Bob with
                the initial inspection done by Manie.
            manie_user_client (Client): The Django test client for Manie.
        """
        link = _get_upload_quote_link_or_none(
            bob_job_with_initial_manie_inspection,
            manie_user_client,
        )
        assert link is not None

        # Confirm that the link goes to the correct URL.
        expected_url = reverse(
            "jobs:quote_upload",
            kwargs={"pk": bob_job_with_initial_manie_inspection.pk},
        )
        assert link["href"] == expected_url
