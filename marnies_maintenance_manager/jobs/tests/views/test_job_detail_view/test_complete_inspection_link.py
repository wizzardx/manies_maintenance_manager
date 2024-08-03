"""Tests for the visibility of the update link in the job detail view.

This module contains tests to ensure that the update link is visible to the correct
users in the job detail view.
"""

from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    _get_page_soup,
)


class TestUpdateLinkVisibility:
    """Tests to ensure that the update link is visible to the correct users."""

    @staticmethod
    def test_page_has_update_link_going_to_update_view(
        job_created_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure that the job detail page has a link to the update view.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        soup = _get_page_soup(job_created_by_bob, marnie_user_client)
        link = soup.find("a", string="Complete Inspection")
        assert link is not None

        # Confirm that the link goes to the correct URL.
        expected_url = reverse(
            "jobs:job_complete_inspection",
            kwargs={"pk": job_created_by_bob.pk},
        )
        assert link["href"] == expected_url

    @staticmethod
    def test_update_link_is_visible_for_admin(
        job_created_by_bob: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the job detail page shows the update link to the admin user.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            admin_client (Client): The Django test client for the admin user.
        """
        soup = _get_page_soup(job_created_by_bob, admin_client)
        link = soup.find("a", string="Complete Inspection")
        assert link is not None

    @staticmethod
    def test_update_link_is_not_visible_for_agent(
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure that the job detail page does not show the update link to agents.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        response = bob_agent_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_200_OK
        page = response.content.decode("utf-8")

        # Use Python BeautifulSoup to parse the HTML and find the link
        # to the job update view.
        soup = BeautifulSoup(page, "html.parser")

        # Check with BeautifulSoup that the link is not present.
        link = soup.find("a", string="Update")
        assert link is None

    @staticmethod
    def test_update_link_is_not_visible_to_marnie_after_he_has_done_initial_inspection(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure Marnie can't see the update link after completing initial inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        response = marnie_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        page = response.content.decode("utf-8")

        # Use Python BeautifulSoup to parse the HTML and find the link with the text
        # "Update"
        soup = BeautifulSoup(page, "html.parser")
        link = soup.find("a", string="Update")

        # Confirm that we couldn't find it:
        assert (
            link is None
        ), "The link to update the job should not be visible to Marnie."
