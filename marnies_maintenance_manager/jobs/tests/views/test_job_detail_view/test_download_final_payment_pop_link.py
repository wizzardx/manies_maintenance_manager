"""Tests for job detail view access and POP link visibility in a Django application.

This module contains tests for the job detail view access and link visibility in the
Marnie's Maintenance Manager application. It ensures various user roles and scenarios
are properly handling the visibility of payment proof of purchase (POP) links according
to the business rules.

The module leverages Django's testing frameworks and other libraries such as pytest and
BeautifulSoup to verify that:
- Anonymous users are redirected to the login page when trying to access job details.
- Agents can only see the POP link if they have uploaded it or are otherwise authorized.
- Specific business roles like Marnie or an admin user have the appropriate visibility.

Functions:
    test_anonymous_user_cannot_reach_page_to_see_link: Test anonymous users' access.
    test_link_not_visible_when_agent_has_not_uploaded_final_payment_pop: Test
        visibility of the link based on upload status.
    get_final_payment_pop_link: Utility to extract the POP link from the job detail
        view HTML.
    test_agent_who_created_job_can_see_link: Ensure creators can see the link.
    test_agent_who_did_not_create_job_cannot_reach_page_to_see_link: Restrict
        unauthorized agents.
    test_marnie_can_see_link: Confirm that Marnie can see the POP link.
    test_admin_can_see_link: Ensure admin users can access the POP link.

Each test and utility function uses Django's `RequestFactory` for simulating HTTP
requests, and assertions are made to check responses against expected outcomes such as
HTTP status codes and HTML contents.
"""

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
    bob_job_with_final_payment_pop: Job,
) -> None:
    """Ensure an anonymous user cannot reach the page to see the link.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
    """
    job = bob_job_with_final_payment_pop
    response = get_job_detail_view_response_for_anonymous_user(job)
    assert response.url == f"/accounts/login/?next=/jobs/{job.pk}/"
    assert response.status_code == status.HTTP_302_FOUND


def test_link_not_visible_when_agent_has_not_uploaded_final_payment_pop(
    job_accepted_by_bob: Job,
    bob_agent_user: User,
) -> None:
    """Ensure link is hidden without final payment POP upload.

    Args:
        job_accepted_by_bob (Job): The job accepted by Bob.
        bob_agent_user (User): The Bob user.
    """
    link = get_final_payment_pop_link(bob_agent_user, job_accepted_by_bob)
    assert link is None


def get_final_payment_pop_link(user: User, job: Job) -> BeautifulSoup:
    """Get the final payment POP link from the job detail view.

    Args:
        user (User): The user requesting the page.
        job (Job): The job to display.

    Returns:
        BeautifulSoup: The link to download the final payment POP.
    """
    soup = fetch_job_detail_view_response(user, job)
    return soup.find("a", string="Download Final Payment POP")


def test_agent_who_created_job_can_see_link(
    bob_job_with_final_payment_pop: Job,
    bob_agent_user: User,
) -> None:
    """Ensure the agent who created the job can see the link.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
        bob_agent_user (User): The Bob user.
    """
    job = bob_job_with_final_payment_pop
    link = get_final_payment_pop_link(bob_agent_user, job)
    assert link is not None
    assert link["href"] == job.final_payment_pop.url


def test_agent_who_did_not_create_job_cannot_reach_page_to_see_link(
    bob_job_with_final_payment_pop: Job,
    alice_agent_user: User,
) -> None:
    """Ensure an agent who didn't create the job cannot reach the page to see the link.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
        alice_agent_user (User): The Alice user.
    """
    job = bob_job_with_final_payment_pop
    with pytest.raises(PermissionDenied):
        create_job_detail_request(alice_agent_user, job)


def test_marnie_can_see_link(
    bob_job_with_final_payment_pop: Job,
    marnie_user: User,
) -> None:
    """Ensure Marnie can see the link.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
        marnie_user (User): The Marnie user.
    """
    job = bob_job_with_final_payment_pop
    link = get_final_payment_pop_link(marnie_user, job)
    assert link is not None
    assert link["href"] == job.final_payment_pop.url


def test_admin_can_see_link(
    bob_job_with_final_payment_pop: Job,
    admin_user: User,
) -> None:
    """Ensure an admin can see the link.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
        admin_user (User): The admin user.
    """
    job = bob_job_with_final_payment_pop
    link = get_final_payment_pop_link(admin_user, job)
    assert link is not None
    assert link["href"] == job.final_payment_pop.url
