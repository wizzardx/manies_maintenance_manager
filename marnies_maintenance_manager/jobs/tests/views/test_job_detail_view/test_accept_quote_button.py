"""Tests for the visibility of the accept quote button in the job detail view.

This module contains tests to ensure that the accept quote button is visible to
the correct users in the job detail view.
"""

from bs4 import BeautifulSoup
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job


class TestAcceptQuoteButtonVisibility:
    """Tests to ensure that the accept quote button is visible to the correct users."""

    @staticmethod
    def test_agent_can_see_accept_quote_button_when_marnie_has_done_initial_inspection(
        bob_job_with_initial_marnie_inspection: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure agent sees accept quote button when Marnie has done the inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            bob_agent_user_client,
        )
        assert button is not None

    @staticmethod
    def test_button_not_visible_when_marnie_has_not_done_initial_inspection(
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the accept quote button is hidden if Marnie hasn't done inspection.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_accept_quote_button_or_none(
            job_created_by_bob,
            bob_agent_user_client,
        )
        assert button is None

    @staticmethod
    def test_marnie_cannot_see_accept_quote_button_after_doing_initial_inspection(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure Marnie can't see the accept quote button after the initial inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            marnie_user_client,
        )
        assert button is None

    @staticmethod
    def test_another_agent_cannot_reach_page_to_see_quote_button(
        bob_job_with_initial_marnie_inspection: Job,
        peter_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't access the detail page.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            peter_agent_user_client (Client): The Django test client for Peter.
        """
        response = peter_agent_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_admin_can_see_accept_quote_button(
        bob_job_with_initial_marnie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can see the accept quote button.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            admin_client (Client): The Django test client for the admin user.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            admin_client,
        )
        assert button is not None

    @staticmethod
    def test_anonymous_user_is_redirected_to_login_page_before_seeing_view(
        bob_job_with_initial_marnie_inspection: Job,
        client: Client,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
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

    @staticmethod
    def test_still_visible_after_rejecting_quote(
        job_rejected_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the accept quote button is visible after the agent rejects quote.

        Args:
            job_rejected_by_bob (Job): The job created by Bob with the quote rejected by
                the agent.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_accept_quote_button_or_none(
            job_rejected_by_bob,
            bob_agent_user_client,
        )
        assert button is not None


def _get_accept_quote_button_or_none(
    job: Job,
    user_client: Client,
) -> BeautifulSoup | None:
    """Get the accept quote button, or None if it couldn't be found.

    Args:
        job (Job): The job to get the accept quote button for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The accept quote button, or None if it couldn't be found.
    """
    response = user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the button
    # to accept the quote.
    soup = BeautifulSoup(page, "html.parser")
    return soup.find("button", string="Accept Quote")
