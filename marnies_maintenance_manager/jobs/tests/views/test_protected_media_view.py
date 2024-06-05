"""Tests for the server protected media view."""

import pytest
from django.http import FileResponse
from django.test import Client
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job


@pytest.mark.django_db()
def test_gets_redirected_to_login_for_anonymous_user(client: Client) -> None:
    """Test anonymous user redirection to login for protected media file access.

    Args:
        client (Client): The Django test client.
    """
    # Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    # {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    # while handling a GET request to the /accounts/login/ URL. We can ignore this
    # for our testing.
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        response = client.get("/media/test.txt", follow=True)
    assert response.redirect_chain == [("/accounts/login/?next=/media/test.txt", 302)]


def test_gets_permission_error_for_agent_user(bob_agent_user_client: Client) -> None:
    """Test permission error for agent user accessing protected media file.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob, the agent user.
    """
    response = bob_agent_user_client.get("/media/test.txt", follow=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_gets_404_not_found_error_for_none_existent_file_for_admin(
    admin_client: Client,
) -> None:
    """Test 404 error for admin accessing non-existent protected media file.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/media/test.txt", follow=True)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_happy_path(
    admin_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Test that an admin user can download a file.

    Args:
        admin_client (Client): The Django test client for the admin user.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = admin_client.get(bob_job_with_initial_marnie_inspection.quote.url)
    assert isinstance(response, FileResponse)

    assert response.status_code == status.HTTP_200_OK
    content = b"".join(response.streaming_content)  # type: ignore[arg-type]
    assert content == bob_job_with_initial_marnie_inspection.quote.read()
