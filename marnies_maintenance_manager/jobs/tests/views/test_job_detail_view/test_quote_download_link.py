"""Tests for the visibility of the quote download link in the job detail view.

This module contains tests to ensure that the quote download link is visible to
the correct users in the job detail view.
"""

from bs4 import BeautifulSoup
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job


def _ensure_can_see_link(user_client: Client, job: Job) -> None:
    """Ensure that the quote download link is visible to the user.

    Args:
        user_client (Client): The Django test client for the user.
        job (Job): The job to check for the quote download link.
    """
    response = user_client.get(
        reverse(
            "jobs:job_detail",
            kwargs={"pk": job.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the link
    # to download the quote.
    soup = BeautifulSoup(page, "html.parser")
    link = soup.find("a", string="Download Quote")
    assert link is not None

    # Confirm that the link goes to the correct URL.
    expected_url = job.quote.url
    assert link["href"] == expected_url


class TestQuoteDownloadLinkVisibility:
    """Tests to ensure that the quote download link is visible to the correct users."""

    @staticmethod
    def test_marnie_can_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure that Marnie can see the quote download link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        _ensure_can_see_link(marnie_user_client, bob_job_with_initial_marnie_inspection)

    @staticmethod
    def test_admin_can_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can see the quote download link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            admin_client (Client): The Django test client for the admin user.
        """
        _ensure_can_see_link(admin_client, bob_job_with_initial_marnie_inspection)

    @staticmethod
    def test_agent_who_created_job_can_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure that the agent who created the job can see the quote download link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        _ensure_can_see_link(
            bob_agent_user_client,
            bob_job_with_initial_marnie_inspection,
        )

    @staticmethod
    def test_agent_who_did_not_create_job_cannot_reach_page_to_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        alice_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't see the quote link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            alice_agent_user_client (Client): The Django test client for Alice.
        """
        response = alice_agent_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_anonymous_user_cannot_reach_page_to_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        client: Client,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            client (Client): The Django test client.
        """
        response = client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_302_FOUND

        # Check that the user is redirected to the login page.
        response2 = check_type(response, HttpResponseRedirect)
        assert (
            response2.url == "/accounts/login/?next=/jobs/"
            f"{bob_job_with_initial_marnie_inspection.pk}/"
        )
