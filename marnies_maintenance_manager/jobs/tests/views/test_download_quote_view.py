"""Tests for the download quote view."""

# pylint: disable=magic-value-comparison

from pathlib import Path

from django.http import FileResponse
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job


class TestAbilityToDownloadQuoteFiles:
    """Tests to ensure that users can download quote files."""

    @staticmethod
    def test_marnie_can_download_quote_files(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure that Marnie can download quote files.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        response = marnie_user_client.get(
            reverse(
                "jobs:download_quote",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_200_OK

        # Download file content
        file_content = response.content
        # Check if the file content is as expected
        assert file_content == bob_job_with_initial_marnie_inspection.quote.read()

    @staticmethod
    def test_download_nonexistent_quote_file_returns_404(
        job_created_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure that trying to download a non-existent quote file returns a 404.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        # Delete the quote file so that it doesn't exist.
        job_created_by_bob.quote.delete()

        response = marnie_user_client.get(
            reverse("jobs:download_quote", kwargs={"pk": job_created_by_bob.pk}),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.content == b"Quote not set for job"

    @staticmethod
    def test_download_quote_from_nonexistent_job_returns_404(
        marnie_user_client: Client,
    ) -> None:
        """Ensure that trying to download a quote from a non-existent job returns a 404.

        Args:
            marnie_user_client (Client): The Django test client for Marnie.
        """
        response = marnie_user_client.get(
            reverse(
                "jobs:download_quote",
                kwargs={"pk": "d865837c-1e99-11ef-a847-cb433af9e531"},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.content == b"Job not found"

    @staticmethod
    def test_admin_can_download_quote_files(
        bob_job_with_initial_marnie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can download quote files.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            admin_client (Client): The Django test client for the admin user.
        """
        _check_user_can_download_quote_files(
            bob_job_with_initial_marnie_inspection,
            admin_client,
        )

    @staticmethod
    def test_agent_who_created_job_can_download_quote_files(
        bob_job_with_initial_marnie_inspection: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure that the agent who created the job can download quote files.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        _check_user_can_download_quote_files(
            bob_job_with_initial_marnie_inspection,
            bob_agent_user_client,
        )

    @staticmethod
    def test_agents_who_did_not_create_job_cannot_download_quote_files(
        peter_agent_user_client: Client,
        bob_job_with_initial_marnie_inspection: Job,
    ) -> None:
        """Ensure that agents who did not create the job cannot download quote files.

        Args:
            peter_agent_user_client (Client): The Django test client for Peter.
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
        """
        response = peter_agent_user_client.get(
            reverse(
                "jobs:download_quote",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.content == b"Access denied"

    @staticmethod
    def test_media_direct_download_link_to_quote_file_is_inaccessible_to_most_users(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure that the direct download link to the quote file is inaccessible.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        # Example URL that we want to restrict access to: /media/quotes/test.pdf

        response = marnie_user_client.get(
            bob_job_with_initial_marnie_inspection.quote.url,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_media_direct_download_link_to_quote_file_is_accessible_to_admins(
        bob_job_with_initial_marnie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that direct download link to quote file is admin-accessible.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            admin_client (Client): The Django test client for the admin user.
        """
        response = check_type(
            admin_client.get(bob_job_with_initial_marnie_inspection.quote.url),
            FileResponse,
        )
        assert response.status_code == status.HTTP_200_OK
        content = b"".join(response.streaming_content)  # type: ignore[arg-type]
        assert content == bob_job_with_initial_marnie_inspection.quote.read()

        # Check the various other attachment-related content headers, too:
        assert response["Content-Type"] == "application/pdf"
        assert response["Content-Length"] == str(len(content))

        attach_basename = Path(bob_job_with_initial_marnie_inspection.quote.name).name
        assert response["Content-Disposition"] == (
            f'attachment; filename="{attach_basename}"'
        )

    @staticmethod
    def test_media_direct_download_link_to_quote_file_is_inaccessible_to_anonymous(
        bob_job_with_initial_marnie_inspection: Job,
        client: Client,
    ) -> None:
        """Ensure that direct download link to quote file is closed to anonymous users.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            client (Client): The Django test client for an anonymous user.
        """
        response = check_type(
            client.get(bob_job_with_initial_marnie_inspection.quote.url),
            HttpResponseRedirect,
        )
        assert response.status_code == status.HTTP_302_FOUND

        # Check the redirection details:
        response2 = check_type(response, HttpResponseRedirect)
        assert response2.url == "/accounts/login/?next=/media/quotes/test.pdf"


def _check_user_can_download_quote_files(job: Job, client: Client) -> None:
    response = client.get(
        reverse(
            "jobs:download_quote",
            kwargs={"pk": job.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.content == job.quote.read()

    # Check the various other attachment-related content headers, too:
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Length"] == str(len(response.content))

    filename = Path(job.quote.name).name
    assert response["Content-Disposition"] == f'attachment; filename="{filename}"'


def test_fails_for_none_get_request(
    bob_agent_user_client: Client,
    bob_job_with_initial_marnie_inspection: Job,
) -> None:
    """Ensure that the download quote view fails for a GET request.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
    """
    response = bob_agent_user_client.post(
        f"/jobs/{bob_job_with_initial_marnie_inspection.id}/download-quote/",
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.content == b"Method not allowed"
