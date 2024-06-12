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
from marnies_maintenance_manager.users.models import User


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


def test_gets_404_not_found_error_for_none_existent_file_for_admin(
    admin_client: Client,
) -> None:
    """Test 404 error for admin accessing non-existent protected media file.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/media/test.txt", follow=True)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_absolute_paths_not_allowed(admin_client: Client) -> None:
    """Test that absolute paths are not allowed.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/media//test.txt", follow=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# @pytest.mark.django_db()
def test_directory_traversals_not_allowed(admin_client: Client) -> None:
    """Test that directory traversals are not allowed.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/media/../test.pdf", follow=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_error_returned_for_none_get_request(admin_client: Client) -> None:
    """Test that an error is returned for a non-GET request.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.post("/media/test.txt", follow=True)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestQuoteDownloadAccess:
    """Tests for downloading quotes."""

    @staticmethod
    def test_anonymous_user_redirected_to_login(
        client: Client,
        bob_job_with_initial_marnie_inspection: Job,
    ) -> None:
        """Test that anonymous users are redirected to the login page.

        Args:
            client (Client): The Django test client.
            bob_job_with_initial_marnie_inspection (Job): The job with an initial
                Marnie inspection.
        """
        job = bob_job_with_initial_marnie_inspection
        # Note: Django-FastDev causes a DeprecationWarning to be logged when using the
        # {% if %} template tag. This is somewhere deep within the Django-Allauth
        # package, while handling a GET request to the /accounts/login/ URL. We can
        # ignore this for our testing.
        with pytest.warns(
            DeprecationWarning,
            match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead "
            "of {% if %}",
        ):
            response = client.get(job.quote.url, follow=True)
        assert response.redirect_chain == [
            ("/accounts/login/?next=/media/quotes/test.pdf", 302),
        ]

    @staticmethod
    def test_marnie_can_download_quote(
        marnie_user_client: Client,
        bob_job_with_initial_marnie_inspection: Job,
    ) -> None:
        """Test that Marnie can download a quote.

        Args:
            marnie_user_client (Client): The Django test client for the Marnie user.
            bob_job_with_initial_marnie_inspection (Job): The job with an initial
                Marnie inspection.
        """
        job = bob_job_with_initial_marnie_inspection
        response = check_type(
            marnie_user_client.get(job.quote.url, follow=True),
            FileResponse,
        )
        assert response.status_code == status.HTTP_200_OK

        # For just Marnie (this is mainly as a smoke test), we do far more thorough
        # checking of the downloaded.

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
            response["Content-Disposition"]
            == f'attachment; filename="{attach_basename}"'
        )

    @staticmethod
    def test_superuser_can_download_quote(
        superuser_client: Client,
        bob_job_with_initial_marnie_inspection: Job,
    ) -> None:
        """Test that superusers can download quotes.

        Args:
            superuser_client (Client): The Django test client for the superuser.
            bob_job_with_initial_marnie_inspection (Job): The job with an initial
                Marnie inspection.
        """
        job = bob_job_with_initial_marnie_inspection
        response = superuser_client.get(job.quote.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_can_download_quote(
        bob_agent_user_client: Client,
        bob_job_with_initial_marnie_inspection: Job,
    ) -> None:
        """Test that agents who originally created the job can download the quote.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_initial_marnie_inspection (Job): The job with an initial agent
                inspection.
        """
        job = bob_job_with_initial_marnie_inspection
        response = bob_agent_user_client.get(job.quote.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_cannot_download_unlinked_quote(
        bob_agent_user_client: Client,
    ) -> None:
        """Test that an agent cannot download a quote that is not linked to a job.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
        """
        response = bob_agent_user_client.get("/media/quotes/test.pdf", follow=True)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_multilinked_quote(
        bob_agent_user_client: Client,
        bob_job_with_initial_marnie_inspection: Job,
        job_created_by_peter: Job,
    ) -> None:
        """Test that an agent cannot download a quote that is linked to multiple jobs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_initial_marnie_inspection (Job): The job with an initial agent
                inspection.
            job_created_by_peter (Job): The job created by Peter.
        """
        job = bob_job_with_initial_marnie_inspection

        # Update another job to have the same quote as the first job, so that we
        # can trigger the error condition and get the wanted 403 error.
        job2 = job_created_by_peter
        job2.quote = job.quote
        job2.save()

        response = bob_agent_user_client.get(job.quote.url, follow=True)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # Agents who did not originally create the job cannot download the quote

    @staticmethod
    def test_other_agent_cannot_download_quote(
        peter_agent_user_client: Client,
        bob_job_with_initial_marnie_inspection: Job,
    ) -> None:
        """Test that agents not originally creating the job cannot download the quote.

        Args:
            peter_agent_user_client (Client): The Django test client for the Peter agent
                user.
            bob_job_with_initial_marnie_inspection (Job): The job with an initial agent
                inspection.
        """
        response = peter_agent_user_client.get(
            bob_job_with_initial_marnie_inspection.quote.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_marnie_cannot_download_files_from_other_directories(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Test that Marnie cannot download files from unknown directories.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        response = marnie_user_client.get(
            bob_job_with_initial_marnie_inspection.quote.url.replace("quotes", "other"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_none_marnie_none_agent_cannot_download_quote(
        bob_job_with_initial_marnie_inspection: Job,
        bob_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that users who are neither Marnie nor agents cannot download quotes.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job with an initial Marnie
                inspection.
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_agent_user (User): The Bob agent user.
        """
        # Before calling the view, we need to turn off the is_agent flag.
        bob_agent_user.is_agent = False
        bob_agent_user.save()

        response = bob_agent_user_client.get(
            bob_job_with_initial_marnie_inspection.quote.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDepositPOPDownloadAccess:
    """Tests for downloading deposit proof of payment."""

    @staticmethod
    def test_marnie_can_download_deposit_proof_of_payment(
        marnie_user_client: Client,
        bob_job_with_deposit_pop: Job,
    ) -> None:
        """Test that Marnie can download deposit proof of payment.

        Args:
            marnie_user_client (Client): The Django test client for the Marnie user.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
        """
        job = bob_job_with_deposit_pop
        response = check_type(
            marnie_user_client.get(job.deposit_proof_of_payment.url, follow=True),
            FileResponse,
        )
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_superuser_can_download_deposit_proof_of_payment(
        superuser_client: Client,
        bob_job_with_deposit_pop: Job,
    ) -> None:
        """Test that superusers can download deposit proof of payment.

        Args:
            superuser_client (Client): The Django test client for the superuser.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
        """
        job = bob_job_with_deposit_pop
        response = superuser_client.get(job.deposit_proof_of_payment.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_can_download_deposit_proof_of_payment(
        bob_agent_user_client: Client,
        bob_job_with_deposit_pop: Job,
    ) -> None:
        """Test that agents who created the job can download the deposit proof.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
        """
        job = bob_job_with_deposit_pop
        response = bob_agent_user_client.get(
            job.deposit_proof_of_payment.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_cannot_download_unlinked_deposit_proof_of_payment(
        bob_agent_user_client: Client,
    ) -> None:
        """Test that agents cannot download unlinked deposit proof of payment.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
        """
        response = bob_agent_user_client.get(
            "/media/deposit_pops/test.pdf",
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_multilinked_deposit_proof_of_payment(
        bob_agent_user_client: Client,
        bob_job_with_deposit_pop: Job,
        job_created_by_peter: Job,
    ) -> None:
        """Test that agents cannot download deposit proofs linked to multiple jobs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
            job_created_by_peter (Job): The job created by Peter.
        """
        job = bob_job_with_deposit_pop

        # Update another job to have the same deposit proof of payment as the first
        # job, so that we can trigger the error condition and get the wanted 403 error.
        job2 = job_created_by_peter
        job2.deposit_proof_of_payment = job.deposit_proof_of_payment
        job2.save()

        response = bob_agent_user_client.get(
            job.deposit_proof_of_payment.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_other_agent_cannot_download_deposit_proof_of_payment(
        peter_agent_user_client: Client,
        bob_job_with_deposit_pop: Job,
    ) -> None:
        """Test that agents not creating the job cannot download deposit proof.

        Args:
            peter_agent_user_client (Client): The Django test client for the Peter agent
                user.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
        """
        response = peter_agent_user_client.get(
            bob_job_with_deposit_pop.deposit_proof_of_payment.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_none_marnie_none_agent_cannot_download_deposit_proof_of_payment(
        bob_job_with_deposit_pop: Job,
        bob_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that users not Marnie or agents cannot download deposit proof.

        Args:
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_agent_user (User): The Bob agent user.
        """
        # Before calling the view, we need to turn off the is_agent flag.
        bob_agent_user.is_agent = False
        bob_agent_user.save()

        response = bob_agent_user_client.get(
            bob_job_with_deposit_pop.deposit_proof_of_payment.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
