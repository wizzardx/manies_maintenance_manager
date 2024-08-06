"""Tests for "Submit Job Documentation" link visibility in the job details page view."""

from django.test import Client
from django.urls import reverse

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    _get_page_soup,
)


def test_link_is_visible_for_manie_after_manie_completed_onsite_work(
    bob_job_with_onsite_work_completed_by_manie: Job,
    manie_user_client: Client,
) -> None:
    """Ensure Manie can see the update link after the agent uploaded the POP.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with the onsite work
            completed by Manie.
        manie_user_client (Client): The Django test client for Manie.
    """
    soup = _get_page_soup(
        bob_job_with_onsite_work_completed_by_manie,
        manie_user_client,
    )
    link = soup.find("a", string="Submit Job Documentation")
    assert link is not None


def test_link_is_not_visible_for_agents(
    bob_job_with_onsite_work_completed_by_manie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure agents cannot see the "Submit Job Documentation" link.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with the onsite work
            completed by Manie.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    soup = _get_page_soup(
        bob_job_with_onsite_work_completed_by_manie,
        bob_agent_user_client,
    )
    link = soup.find("a", string="Submit Job Documentation")
    assert link is None


def test_link_is_visible_for_admins(
    bob_job_with_onsite_work_completed_by_manie: Job,
    admin_client: Client,
) -> None:
    """Ensure admins can see the update link.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with the onsite work
            completed by Manie.
        admin_client (Client): The Django test client for the admin user.
    """
    soup = _get_page_soup(bob_job_with_onsite_work_completed_by_manie, admin_client)
    link = soup.find("a", string="Submit Job Documentation")
    assert link is not None


def test_link_points_to_submit_job_documentation_page(
    bob_job_with_onsite_work_completed_by_manie: Job,
    manie_user_client: Client,
) -> None:
    """Ensure the update link points to the "Submit Job Documentation" page.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with the onsite work
            completed by Manie.
        manie_user_client (Client): The Django test client for Manie.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    soup = _get_page_soup(job, manie_user_client)
    link = soup.find("a", string="Submit Job Documentation")
    assert link is not None
    expected_url = reverse(
        "jobs:job_submit_documentation",
        kwargs={"pk": job.pk},
    )
    assert link["href"] == expected_url
