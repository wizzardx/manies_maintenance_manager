"""Utility functions for the job detail view tests."""

from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseBase
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.job_detail_view import JobDetailView
from marnies_maintenance_manager.users.models import User


def _get_page_soup(job: Job, user_client: Client) -> BeautifulSoup:
    """Get the parsed HTML of the job detail page for a given user.

    Args:
        job (Job): The job to get the page for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup: The BeautifulSoup object representing the parsed HTML content.
    """
    response = user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")
    return BeautifulSoup(page, "html.parser")


def _get_update_link_or_none(job: Job, user_client: Client) -> BeautifulSoup | None:
    """Get the link to the job update view, or None if it couldn't be found.

    Args:
        job (Job): The job to get the update link for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The link to the job update view, or None if it couldn't
    """
    soup = _get_page_soup(job, user_client)
    return soup.find("a", string="Update")


def fetch_job_detail_view_response(user: User, job: Job) -> BeautifulSoup:
    """Fetch the job detail view response for a given user and job.

    Args:
        user (User): The user requesting the page.
        job (Job): The job to display.

    Returns:
        BeautifulSoup: The BeautifulSoup object representing the parsed HTML content.
    """
    request = RequestFactory().get(reverse("jobs:job_detail", kwargs={"pk": job.pk}))
    request.user = user
    response = check_type(
        JobDetailView.as_view()(request, pk=job.pk),
        TemplateResponse,
    )
    assert response.status_code == status.HTTP_200_OK
    return BeautifulSoup(response.render().content, "html.parser")


def create_job_detail_request(user: User, job: Job) -> HttpResponseBase:
    """Create a job detail request and return the response.

    Args:
        user (User): The user making the request.
        job (Job): The job to display.

    Returns:
        HttpResponseBase: The response from the job detail view.
    """
    request = RequestFactory().get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    request.user = user
    return JobDetailView.as_view()(request, pk=job.pk)


def get_job_detail_view_response_for_anonymous_user(job: Job) -> HttpResponseRedirect:
    """Get the job detail view response for an anonymous user.

    Args:
        job (Job): The job instance for which to get the detail view response.

    Returns:
        HttpResponseRedirect: The response redirecting to the login page.
    """
    request = RequestFactory().get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    request.user = AnonymousUser()
    return check_type(
        JobDetailView.as_view()(request, pk=job.pk),
        HttpResponseRedirect,
    )


def assert_anonymous_user_redirected_to_login(job: Job, client: Client) -> None:
    """Assert anonymous user redirection to login page.

    Args:
        job (Job): The job instance.
        client (Client): The Django test client.
    """
    response = client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_302_FOUND

    # Check that the user is redirected to the login page.
    response2 = check_type(response, HttpResponseRedirect)
    assert response2.url == f"/accounts/login/?next=/jobs/{job.pk}/"


def _get_reject_quote_button_or_none(
    job: Job,
    user_client: Client,
) -> BeautifulSoup | None:
    """Get the reject quote button, or None if it couldn't be found.

    Args:
        job (Job): The job to get the reject quote button for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The reject quote button, or None if it couldn't be found.
    """
    soup = _get_page_soup(job, user_client)
    return soup.find("button", string="Reject Quote")


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
    soup = _get_page_soup(job, user_client)
    return soup.find("button", string="Accept Quote")


def assert_agent_cannot_access_job_detail(client: Client, job: Job) -> None:
    """Assert that an agent cannot access the job detail view.

    Args:
        client (Client): The Django test client for the agent.
        job (Job): The job instance.
    """
    response = client.get(
        reverse(
            "jobs:job_detail",
            kwargs={"pk": job.pk},
        ),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
