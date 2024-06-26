"""Tests for the download deposit POP link on the job detail view."""

# pylint: disable=magic-value-comparison

import pytest
from bs4 import BeautifulSoup
from django.core.exceptions import PermissionDenied
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    create_job_detail_request,
)
from marnies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    fetch_job_detail_view_response,
)
from marnies_maintenance_manager.jobs.tests.views.test_job_detail_view.utils import (
    get_job_detail_view_response_for_anonymous_user,
)
from marnies_maintenance_manager.users.models import User


def test_anonymous_user_cannot_reach_page_to_see_link(
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure that an anonymous user cannot reach the page to see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit
            uploaded.
    """
    job = bob_job_with_deposit_pop
    response = get_job_detail_view_response_for_anonymous_user(job)
    assert response.url == f"/accounts/login/?next={job.get_absolute_url()}"
    assert response.status_code == status.HTTP_302_FOUND


def test_link_not_visible_when_agent_has_not_uploaded_deposit_pop(
    job_accepted_by_bob: Job,
    bob_agent_user: User,
) -> None:
    """Ensure the link is not visible when the agent hasn't uploaded the deposit POP.

    Args:
        job_accepted_by_bob (Job): The job accepted by Bob.
        bob_agent_user (User): The Bob user.
    """
    link = get_deposit_pop_link(bob_agent_user, job_accepted_by_bob)
    assert link is None


def get_deposit_pop_link(user: User, job: Job) -> BeautifulSoup:
    """Get the deposit POP link from the job detail view.

    Args:
        user (User): The user requesting the page.
        job (Job): The job to display.

    Returns:
        BeautifulSoup: The BeautifulSoup object representing the link.
    """
    soup = fetch_job_detail_view_response(user, job)
    return soup.find("a", string="Download Deposit POP")


def test_agent_who_created_job_can_see_link(
    bob_job_with_deposit_pop: Job,
    bob_agent_user: User,
) -> None:
    """Ensure that the agent who created the job can see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit pop
            uploaded.
        bob_agent_user (User): The Bob user.
    """
    job = bob_job_with_deposit_pop
    link = get_deposit_pop_link(bob_agent_user, job)
    assert link is not None

    # Also check the URL itself.
    assert link.get("href") == job.deposit_proof_of_payment.url


def test_agent_who_did_not_create_job_cannot_reach_page_to_see_link(
    bob_job_with_deposit_pop: Job,
    alice_agent_user: User,
) -> None:
    """Ensure an agent who didn't create the job cannot reach the page to see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit pop
            uploaded.
        alice_agent_user (User): The Alice user.
    """
    job = bob_job_with_deposit_pop
    with pytest.raises(PermissionDenied):
        create_job_detail_request(alice_agent_user, job)


# Marnie can see the link.
def test_marnie_can_see_link(bob_job_with_deposit_pop: Job, marnie_user: User) -> None:
    """Ensure that Marnie can see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit pop
            uploaded.
        marnie_user (User): The Marnie user.
    """
    job = bob_job_with_deposit_pop
    link = get_deposit_pop_link(marnie_user, job)
    assert link is not None

    # Also check the URL itself.
    assert link["href"] == job.deposit_proof_of_payment.url


# Admins can see the link.
def test_admin_can_see_link(bob_job_with_deposit_pop: Job, admin_user: User) -> None:
    """Ensure that the admin can see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit pop
            uploaded.
        admin_user (User): The admin user.
    """
    job = bob_job_with_deposit_pop
    link = get_deposit_pop_link(admin_user, job)
    assert link is not None

    # Also check the URL itself.
    assert link["href"] == job.deposit_proof_of_payment.url
