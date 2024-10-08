"""Tests for the visibility of the quote download link in the job detail view.

This module contains tests to ensure that the quote download link is visible to
the correct users in the job detail view.
"""

from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    _get_page_soup,
)


def _ensure_can_see_link(user_client: Client, job: Job) -> None:
    """Ensure that the quote download link is visible to the user.

    Args:
        user_client (Client): The Django test client for the user.
        job (Job): The job to check for the quote download link.
    """
    soup = _get_page_soup(job, user_client)
    link = soup.find("a", string="Download Quote")
    assert link is not None

    # Confirm that the link goes to the correct URL.
    expected_url = job.quote.url
    assert link["href"] == expected_url


class TestQuoteDownloadLinkVisibility:
    """Tests to ensure that the quote download link is visible to the correct users."""

    @staticmethod
    def test_manie_can_see_link(
        bob_job_with_quote: Job,
        manie_user_client: Client,
    ) -> None:
        """Ensure that Manie can see the quote download link.

        Args:
            bob_job_with_quote (Job): The job created by Bob with
                the initial inspection done by Manie.
            manie_user_client (Client): The Django test client for Manie.
        """
        _ensure_can_see_link(manie_user_client, bob_job_with_quote)

    @staticmethod
    def test_admin_can_see_link(
        bob_job_with_quote: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can see the quote download link.

        Args:
            bob_job_with_quote (Job): The job created by Bob, with Manie's quote
                uploaded.
            admin_client (Client): The Django test client for the admin user.
        """
        _ensure_can_see_link(admin_client, bob_job_with_quote)

    @staticmethod
    def test_agent_who_created_job_can_see_link(
        bob_job_with_quote: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure that the agent who created the job can see the quote download link.

        Args:
            bob_job_with_quote (Job): The job created by Bob, with Manie's quote
                uploaded.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        _ensure_can_see_link(
            bob_agent_user_client,
            bob_job_with_quote,
        )

    @staticmethod
    def test_agent_who_did_not_create_job_cannot_reach_page_to_see_link(
        bob_job_with_quote: Job,
        alice_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't see the quote link.

        Args:
            bob_job_with_quote (Job): The job created by Bob, with Manie's quote
                uploaded.
            alice_agent_user_client (Client): The Django test client for Alice.
        """
        response = alice_agent_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_quote.pk},
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_anonymous_user_cannot_reach_page_to_see_link(
        bob_job_with_quote: Job,
        client: Client,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            bob_job_with_quote (Job): The job created by Bob, with Manie's quote
                uploaded.
            client (Client): The Django test client.
        """
        response = client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_quote.pk},
            ),
        )
        assert response.status_code == status.HTTP_302_FOUND

        # Check that the user is redirected to the login page.
        response2 = check_type(response, HttpResponseRedirect)
        assert response2.url == (
            "/accounts/login/?next=/jobs/" + f"{bob_job_with_quote.pk}/"
        )
