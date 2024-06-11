"""Tests for the download deposit POP link on the job detail view."""

# pylint: disable=magic-value-comparison

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.job_detail_view import JobDetailView
from marnies_maintenance_manager.users.models import User


def test_anonymous_user_cannot_reach_page_to_see_link(
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure that an anonymous user cannot reach the page to see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit
            uploaded.
    """
    request = RequestFactory().get(
        reverse("jobs:job_detail", kwargs={"pk": bob_job_with_deposit_pop.pk}),
    )
    request.user = AnonymousUser()
    response = check_type(
        JobDetailView.as_view()(request, pk=bob_job_with_deposit_pop.pk),
        HttpResponseRedirect,
    )
    assert response.url == f"/accounts/login/?next=/jobs/{bob_job_with_deposit_pop.pk}/"
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
    request = RequestFactory().get(reverse("jobs:job_detail", kwargs={"pk": job.pk}))
    request.user = user
    response = check_type(
        JobDetailView.as_view()(request, pk=job.pk),
        TemplateResponse,
    )
    assert response.status_code == status.HTTP_200_OK
    # Use BeautifulSoup to parse the response content and retrieve the link.
    soup = BeautifulSoup(response.render().content, "html.parser")
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
    link = get_deposit_pop_link(bob_agent_user, bob_job_with_deposit_pop)
    assert link is not None

    # Also check the URL itself.
    assert link.get("href") == "/media/deposit_pops/test.pdf"


def test_agent_who_did_not_create_job_cannot_reach_page_to_see_link(
    bob_job_with_deposit_pop: Job,
    peter_agent_user: User,
) -> None:
    """Ensure an agent who didn't create the job cannot reach the page to see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit pop
            uploaded.
        peter_agent_user (User): The Peter user.
    """
    request = RequestFactory().get(
        reverse("jobs:job_detail", kwargs={"pk": bob_job_with_deposit_pop.pk}),
    )
    request.user = peter_agent_user
    with pytest.raises(PermissionDenied):
        JobDetailView.as_view()(request, pk=bob_job_with_deposit_pop.pk)


# Marnie can see the link.
def test_marnie_can_see_link(bob_job_with_deposit_pop: Job, marnie_user: User) -> None:
    """Ensure that Marnie can see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit pop
            uploaded.
        marnie_user (User): The Marnie user.
    """
    link = get_deposit_pop_link(marnie_user, bob_job_with_deposit_pop)
    assert link is not None

    # Also check the URL itself.
    assert link.get("href") == "/media/deposit_pops/test.pdf"


# Admins can see the link.
def test_admin_can_see_link(bob_job_with_deposit_pop: Job, admin_user: User) -> None:
    """Ensure that the admin can see the link.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit pop
            uploaded.
        admin_user (User): The admin user.
    """
    link = get_deposit_pop_link(admin_user, bob_job_with_deposit_pop)
    assert link is not None

    # Also check the URL itself.
    assert link.get("href") == "/media/deposit_pops/test.pdf"
