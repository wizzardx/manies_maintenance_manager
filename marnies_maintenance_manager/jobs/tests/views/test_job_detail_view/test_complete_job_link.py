"""Tests for the update link visibility for the job detail view."""

from django.test import Client
from django.urls import reverse

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    _get_page_soup,
)


def test_is_visible_for_marnie_after_admin_uploaded_pop(
    bob_job_with_deposit_pop: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure Marnie can see the update link after the admin uploaded the POP.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    soup = _get_page_soup(bob_job_with_deposit_pop, marnie_user_client)
    link = soup.find("a", string="Complete Job")
    assert link is not None


def test_is_not_visible_for_agents(
    bob_job_with_deposit_pop: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure agents cannot see the update link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    soup = _get_page_soup(bob_job_with_deposit_pop, bob_agent_user_client)
    link = soup.find("a", string="Complete Job")
    assert link is None


def test_is_visible_for_admins(
    bob_job_with_deposit_pop: Job,
    admin_client: Client,
) -> None:
    """Ensure admins can see the update link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        admin_client (Client): The Django test client for the admin user.
    """
    soup = _get_page_soup(bob_job_with_deposit_pop, admin_client)
    link = soup.find("a", string="Complete Job")
    assert link is not None


def test_points_to_complete_the_jop_page(
    bob_job_with_deposit_pop: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure the update link points to the complete the job page.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    soup = _get_page_soup(bob_job_with_deposit_pop, marnie_user_client)
    link = soup.find("a", string="Complete Job")
    assert link is not None
    expected_url = reverse(
        "jobs:job_complete",
        kwargs={"pk": bob_job_with_deposit_pop.pk},
    )
    assert link["href"] == expected_url
