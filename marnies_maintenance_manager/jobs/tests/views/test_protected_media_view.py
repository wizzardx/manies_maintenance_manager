"""Tests for the server protected media view."""

# pylint: disable=magic-value-comparison

from collections.abc import Iterator
from pathlib import Path

import pytest
from django.http import FileResponse
from django.test import Client
from rest_framework import status
from typeguard import check_type

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
    assert response.content == b"Access denied"


def test_gets_404_not_found_error_for_none_existent_file_for_admin(
    admin_client: Client,
) -> None:
    """Test 404 error for admin accessing non-existent protected media file.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/media/test.txt", follow=True)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_admin_user_can_download_files(
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


def test_marnie_can_download_quote_files(
    marnie_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Test that Marnie can download a quote file.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = check_type(
        marnie_user_client.get(bob_job_with_initial_marnie_inspection.quote.url),
        FileResponse,
    )
    assert response.status_code == status.HTTP_200_OK

    streaming_content = check_type(response.streaming_content, Iterator[bytes])
    content = b"".join(streaming_content)
    assert content == bob_job_with_initial_marnie_inspection.quote.read()

    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Length"] == str(len(content))

    attach_relpath = Path(bob_job_with_initial_marnie_inspection.quote.name)
    assert attach_relpath == Path("quotes/test.pdf")
    attach_basename = attach_relpath.name

    assert attach_basename == "test.pdf"
    assert (
        response["Content-Disposition"] == f'attachment; filename="{attach_basename}"'
    )


def test_marnie_cannot_download_none_pdfs_in_quotes_directory(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
) -> None:
    """Test that Marnie cannot download non-PDF files in the quotes directory.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    response = marnie_user_client.get(
        bob_job_with_initial_marnie_inspection.quote.url.replace(".pdf", ".txt"),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content == b"Access denied"


def test_marnie_cannot_download_files_in_other_directories(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
) -> None:
    """Test that Marnie cannot download files in other directories.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    response = marnie_user_client.get(
        bob_job_with_initial_marnie_inspection.quote.url.replace("quotes", "other"),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content == b"Access denied"


def test_absolute_paths_not_allowed(admin_client: Client) -> None:
    """Test that absolute paths are not allowed.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/media//test.txt", follow=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db()
def test_directory_traversals_not_allowed(admin_client: Client) -> None:
    """Test that directory traversals are not allowed.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/media/../test.pdf", follow=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.content == b"Access denied"
