"""Tests for the visibility of the accept quote button in the job detail view.

This module contains tests to ensure that the accept quote button is visible to
the correct users in the job detail view.
"""

from django.test import Client

from manies_maintenance_manager.jobs.models import Job

from .utils import _get_accept_quote_button_or_none
from .utils import assert_agent_cannot_access_job_detail
from .utils import assert_anonymous_user_redirected_to_login


class TestAcceptQuoteButtonVisibility:
    """Tests to ensure that the accept quote button is visible to the correct users."""

    @staticmethod
    def test_agent_can_see_accept_quote_button_when_manie_has_uploaded_quote(
        bob_job_with_quote: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure agent sees accept quote button when Manie has done the inspection.

        Args:
            bob_job_with_quote (Job): The job created by Bob with the quote uploaded.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_quote,
            bob_agent_user_client,
        )
        assert button is not None

    @staticmethod
    def test_button_not_visible_when_manie_has_not_uploaded_quote(
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the accept quote button is hidden if Manie hasn't done inspection.

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
    def test_manie_cannot_see_accept_quote_button_after_uploading_quote(
        bob_job_with_quote: Job,
        manie_user_client: Client,
    ) -> None:
        """Ensure Manie can't see the accept quote button after uploading a quote.

        Args:
            bob_job_with_quote (Job): The job created by Bob with the quote uploaded.
            manie_user_client (Client): The Django test client for Manie.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_quote,
            manie_user_client,
        )
        assert button is None

    @staticmethod
    def test_another_agent_cannot_reach_page_to_see_quote_button(
        bob_job_with_quote: Job,
        alice_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't access the detail page.

        Args:
            bob_job_with_quote (Job): The job created by Bob with the quote uploaded.
            alice_agent_user_client (Client): The Django test client for Alice.
        """
        assert_agent_cannot_access_job_detail(
            alice_agent_user_client,
            bob_job_with_quote,
        )

    @staticmethod
    def test_admin_can_see_accept_quote_button(
        bob_job_with_quote: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can see the accept quote button.

        Args:
            bob_job_with_quote (Job): The job created by Bob with the quote uploaded.
            admin_client (Client): The Django test client for the admin user.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_quote,
            admin_client,
        )
        assert button is not None

    @staticmethod
    def test_anonymous_user_is_redirected_to_login_page(
        bob_job_with_quote: Job,
        client: Client,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            bob_job_with_quote (Job): The job created by Bob with the quote uploaded.
            client (Client): The Django test client.
        """
        assert_anonymous_user_redirected_to_login(
            bob_job_with_quote,
            client,
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
