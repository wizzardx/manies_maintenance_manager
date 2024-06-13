"""Tests for the update link visibility for the job detail view."""

from django.test import Client

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    _get_update_link_or_none,
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
    link = _get_update_link_or_none(bob_job_with_deposit_pop, marnie_user_client)
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
    link = _get_update_link_or_none(bob_job_with_deposit_pop, bob_agent_user_client)
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
    link = _get_update_link_or_none(bob_job_with_deposit_pop, admin_client)
    assert link is not None
