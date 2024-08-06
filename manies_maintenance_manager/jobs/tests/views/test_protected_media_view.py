"""Tests for the server protected media view."""

# pylint: disable=magic-value-comparison
# ruff: noqa: ERA001

from collections.abc import Iterator
from pathlib import Path

import pytest
from django.http import FileResponse
from django.test import Client
from rest_framework import status
from typeguard import check_type

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.models import JobCompletionPhoto
from manies_maintenance_manager.jobs.tests.views.conftest import (
    BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS,
)
from manies_maintenance_manager.jobs.utils import safe_read
from manies_maintenance_manager.users.models import User


@pytest.mark.django_db()
def test_gets_are_not_permitted_for_anonymous_user(client: Client) -> None:
    """Test permission denied for anonymous user access to private media files.

    Args:
        client (Client): The Django test client.
    """
    response = client.get("/private-media/test.txt")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_gets_404_not_found_error_for_none_existent_file_for_admin(
    admin_client: Client,
) -> None:
    """Test 404 error for admin accessing non-existent protected media file.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/private-media/test.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_absolute_paths_not_allowed(admin_client: Client) -> None:
    """Test that absolute paths are not allowed.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/private-media//test.txt")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_directory_traversals_not_allowed(admin_client: Client) -> None:
    """Test that directory traversals are not allowed.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get("/private-media/../test.pdf")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_error_returned_for_none_get_request(admin_client: Client) -> None:
    """Test that an error is returned for a non-GET request.

    Args:
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.post("/private-media/test.txt", follow=True)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def trigger_multilinked_error(
    client: Client,
    job1: Job,
    job2: Job,
    file_attr: str,
    expected_status: int = status.HTTP_403_FORBIDDEN,
) -> None:
    """Trigger the multilinked error condition.

    Args:
        client (Client): The Django test client.
        job1 (Job): The first job instance.
        job2 (Job): The second job instance to link the same file.
        file_attr (str): The file attribute to link (e.g., 'quote', 'invoice').
        expected_status (int): The expected HTTP status code. Defaults to 403.
    """
    # Update another job (or job completion photo) to have the same file as the first
    # job (or job completion photo), so that we can trigger the error condition and get
    # the wanted status error.

    if file_attr == "job_completion_photo":
        first_job_completion_photo = check_type(
            job1.job_completion_photos.first(),
            JobCompletionPhoto,
        )
        job2.job_completion_photos.create(
            photo=first_job_completion_photo.photo,
        )
    else:
        setattr(job2, file_attr, getattr(job1, file_attr))
    job2.save()

    if file_attr == "job_completion_photo":
        first_job_completion_photo = check_type(
            job1.job_completion_photos.first(),
            JobCompletionPhoto,
        )
        file_url = first_job_completion_photo.photo.url
    else:
        file_url = getattr(job1, file_attr).url
    response = client.get(file_url, follow=True)
    assert response.status_code == expected_status


class TestQuoteDownloadAccess:
    """Tests for downloading quotes."""

    @staticmethod
    def test_anonymous_user_not_permitted(
        client: Client,
        bob_job_with_quote: Job,
    ) -> None:
        """Test that anonymous users are not permitted to download the file.

        Args:
            client (Client): The Django test client.
            bob_job_with_quote (Job): The job with Manie's quote attached.
        """
        job = bob_job_with_quote
        response = client.get(job.quote.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_manie_can_download_quote(
        manie_user_client: Client,
        bob_job_with_quote: Job,
    ) -> None:
        """Test that Manie can download a quote.

        Args:
            manie_user_client (Client): The Django test client for the Manie user.
            bob_job_with_quote (Job): The job with Manie's quote attached.
        """
        job = bob_job_with_quote
        response = check_type(
            manie_user_client.get(job.quote.url, follow=True),
            FileResponse,
        )
        assert response.status_code == status.HTTP_200_OK

        # For just Manie (this is mainly as a smoke test), we do far more thorough
        # checking of the downloaded.

        streaming_content = check_type(response.streaming_content, Iterator[bytes])
        content = b"".join(streaming_content)
        quote = bob_job_with_quote.quote
        with safe_read(quote):
            assert content == quote.read()

        assert response["Content-Type"] == "application/pdf"
        assert response["Content-Length"] == str(len(content))

        attach_relpath = Path(bob_job_with_quote.quote.name)
        # eg: attach_relpath = PosixPath('quotes/test_ISjWJsF.pdf'

        attach_basename = attach_relpath.name
        # eg: attach_basename = "test_ISjWJsF.pdf"

        assert attach_relpath.parent == Path("quotes")
        assert attach_relpath.name.startswith("test")
        assert attach_relpath.suffix == ".pdf"

        assert attach_basename.startswith("test")
        assert attach_basename.endswith(".pdf")

        assert (
            response["Content-Disposition"] == f'inline; filename="{attach_basename}"'
        )

    @staticmethod
    def test_superuser_can_download_quote(
        superuser_client: Client,
        bob_job_with_quote: Job,
    ) -> None:
        """Test that superusers can download quotes.

        Args:
            superuser_client (Client): The Django test client for the superuser.
            bob_job_with_quote (Job): The job with Manie's quote attached.
        """
        job = bob_job_with_quote
        response = superuser_client.get(job.quote.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_can_download_quote(
        bob_agent_user_client: Client,
        bob_job_with_quote: Job,
    ) -> None:
        """Test that agents who originally created the job can download the quote.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_quote (Job): The job with Manies quote attached.
        """
        job = bob_job_with_quote
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
        response = bob_agent_user_client.get(
            "/private-media/quotes/test.pdf",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_multilinked_quote(
        bob_agent_user_client: Client,
        bob_job_with_quote: Job,
        job_created_by_alice: Job,
    ) -> None:
        """Test that an agent cannot download a quote that is linked to multiple jobs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_quote (Job): The job with Manie's quote attached.
            job_created_by_alice (Job): The job created by Alice.
        """
        trigger_multilinked_error(
            bob_agent_user_client,
            bob_job_with_quote,
            job_created_by_alice,
            "quote",
        )

    # Agents who did not originally create the job cannot download the quote

    @staticmethod
    def test_other_agent_cannot_download_quote(
        alice_agent_user_client: Client,
        bob_job_with_quote: Job,
    ) -> None:
        """Test that agents not originally creating the job cannot download the quote.

        Args:
            alice_agent_user_client (Client): The Django test client for the Alice agent
                user.
            bob_job_with_quote (Job): The job with Manie's quote attached.
        """
        response = alice_agent_user_client.get(
            bob_job_with_quote.quote.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_manie_cannot_download_files_from_other_directories(
        bob_job_with_quote: Job,
        manie_user_client: Client,
    ) -> None:
        """Test that Manie cannot download files from unknown directories.

        Args:
            bob_job_with_quote (Job): The job with Manie's quote attached.
            manie_user_client (Client): The Django test client for Manie.
        """
        response = manie_user_client.get(
            bob_job_with_quote.quote.url.replace("quotes", "other"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_none_manie_none_agent_cannot_download_quote(
        bob_job_with_quote: Job,
        bob_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that users who are neither Manie nor agents cannot download quotes.

        Args:
            bob_job_with_quote (Job): The job with Manie's quote attached.
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_agent_user (User): The Bob agent user.
        """
        # Before calling the view, we need to turn off the is_agent flag.
        bob_agent_user.is_agent = False
        bob_agent_user.save()

        response = bob_agent_user_client.get(
            bob_job_with_quote.quote.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDepositPOPDownloadAccess:
    """Tests for downloading deposit proof of payment."""

    @staticmethod
    def test_manie_can_download_deposit_proof_of_payment(
        manie_user_client: Client,
        bob_job_with_deposit_pop: Job,
    ) -> None:
        """Test that Manie can download deposit proof of payment.

        Args:
            manie_user_client (Client): The Django test client for the Manie user.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
        """
        job = bob_job_with_deposit_pop
        response = check_type(
            manie_user_client.get(job.deposit_proof_of_payment.url, follow=True),
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
            "/private-media/deposit_pops/test.pdf",
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_multilinked_deposit_proof_of_payment(
        bob_agent_user_client: Client,
        bob_job_with_deposit_pop: Job,
        job_created_by_alice: Job,
    ) -> None:
        """Test that agents cannot download deposit proofs linked to multiple jobs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
            job_created_by_alice (Job): The job created by Alice.
        """
        trigger_multilinked_error(
            bob_agent_user_client,
            bob_job_with_deposit_pop,
            job_created_by_alice,
            "deposit_proof_of_payment",
        )

    @staticmethod
    def test_other_agent_cannot_download_deposit_proof_of_payment(
        alice_agent_user_client: Client,
        bob_job_with_deposit_pop: Job,
    ) -> None:
        """Test that agents not creating the job cannot download deposit proof.

        Args:
            alice_agent_user_client (Client): The Django test client for the Alice agent
                user.
            bob_job_with_deposit_pop (Job): The job with a deposit proof of payment.
        """
        response = alice_agent_user_client.get(
            bob_job_with_deposit_pop.deposit_proof_of_payment.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_none_manie_none_agent_cannot_download_deposit_proof_of_payment(
        bob_job_with_deposit_pop: Job,
        bob_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that users not Manie or agents cannot download deposit proof.

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


class TestInvoiceDownloadAccess:
    """Tests for downloading invoices."""

    @staticmethod
    def test_manie_can_download_invoice(
        manie_user_client: Client,
        bob_job_with_manie_final_documentation: Job,
    ) -> None:
        """Test that Manie can download invoices.

        Args:
            manie_user_client (Client): The Django test client for the Manie user.
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
        """
        job = bob_job_with_manie_final_documentation
        response = manie_user_client.get(job.invoice.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_superuser_can_download_invoice(
        superuser_client: Client,
        bob_job_with_manie_final_documentation: Job,
    ) -> None:
        """Test that superusers can download invoices.

        Args:
            superuser_client (Client): The Django test client for the superuser.
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
        """
        job = bob_job_with_manie_final_documentation
        response = superuser_client.get(job.invoice.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_can_download_invoice(
        bob_agent_user_client: Client,
        bob_job_with_manie_final_documentation: Job,
    ) -> None:
        """Test that agents who created the job can download the invoice.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
        """
        job = bob_job_with_manie_final_documentation
        response = bob_agent_user_client.get(job.invoice.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_other_agent_cannot_download_invoice(
        alice_agent_user_client: Client,
        bob_job_with_manie_final_documentation: Job,
    ) -> None:
        """Test that agents not creating the job cannot download invoices.

        Args:
            alice_agent_user_client (Client): The Django test client for the Alice agent
                user.
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
        """
        response = alice_agent_user_client.get(
            bob_job_with_manie_final_documentation.invoice.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_none_manie_none_agent_cannot_download_invoice(
        bob_job_with_manie_final_documentation: Job,
        bob_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that users not Manie or agents cannot download invoices.

        Args:
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_agent_user (User): The Bob agent user.
        """
        bob_agent_user.is_agent = False
        bob_agent_user.save()

        response = bob_agent_user_client.get(
            bob_job_with_manie_final_documentation.invoice.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_unlinked_invoice(
        bob_agent_user_client: Client,
    ) -> None:
        """Test that agents cannot download unlinked invoices.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
        """
        response = bob_agent_user_client.get(
            "/private-media/invoices/test.pdf",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_multilinked_invoice(
        bob_agent_user_client: Client,
        bob_job_with_manie_final_documentation: Job,
        job_created_by_alice: Job,
    ) -> None:
        """Test that agents cannot download invoices linked to multiple jobs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_manie_final_documentation (Job): Job with Manies final
                documentation added to it.
            job_created_by_alice (Job): The job created by Alice.
        """
        trigger_multilinked_error(
            bob_agent_user_client,
            bob_job_with_manie_final_documentation,
            job_created_by_alice,
            "invoice",
        )


class TestFinalPaymentPOPDownloadAccess:
    """Tests for downloading Final Payment POPs."""

    @staticmethod
    def test_manie_can_download(
        bob_job_with_final_payment_pop: Job,
        manie_user_client: Client,
    ) -> None:
        """Test that Manie can download Final Payment POPs.

        Args:
            bob_job_with_final_payment_pop (Job): The job with a Final Payment POP.
            manie_user_client (Client): The Django test client for the Manie user.
        """
        job = bob_job_with_final_payment_pop
        response = manie_user_client.get(job.final_payment_pop.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_superuser_can_download(
        bob_job_with_final_payment_pop: Job,
        superuser_client: Client,
    ) -> None:
        """Test that superusers can download Final Payment POPs.

        Args:
            bob_job_with_final_payment_pop (Job): The job with a Final Payment POP.
            superuser_client (Client): The Django test client for the superuser.
        """
        job = bob_job_with_final_payment_pop
        response = superuser_client.get(job.final_payment_pop.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_can_download(
        bob_agent_user_client: Client,
        bob_job_with_final_payment_pop: Job,
    ) -> None:
        """Test that agents who created the job can download the Final Payment POP.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_final_payment_pop (Job): The job with a Final Payment POP.
        """
        job = bob_job_with_final_payment_pop
        response = bob_agent_user_client.get(job.final_payment_pop.url, follow=True)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_other_agent_cannot_download(
        alice_agent_user_client: Client,
        bob_job_with_final_payment_pop: Job,
    ) -> None:
        """Test that agents not creating the job cannot download Final Payment POPs.

        Args:
            alice_agent_user_client (Client): The Django test client for the Alice agent
                user.
            bob_job_with_final_payment_pop (Job): The job with a Final Payment POP.
        """
        response = alice_agent_user_client.get(
            bob_job_with_final_payment_pop.final_payment_pop.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_none_manie_none_agent_cannot_download_final_payment_pops(
        bob_job_with_final_payment_pop: Job,
        bob_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that users not Manie or agents cannot download Final Payment POPs.

        Args:
            bob_job_with_final_payment_pop (Job): The job with a Final Payment POP.
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_agent_user (User): The Bob agent user.
        """
        bob_agent_user.is_agent = False
        bob_agent_user.save()

        response = bob_agent_user_client.get(
            bob_job_with_final_payment_pop.final_payment_pop.url,
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_unlinked_file(
        bob_agent_user_client: Client,
    ) -> None:
        """Test that agents cannot download unlinked Final Payment POPs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
        """
        response = bob_agent_user_client.get(
            "/private-media/final_payment_pops/test.pdf",
            follow=True,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_multilinked_file(
        bob_agent_user_client: Client,
        bob_job_with_final_payment_pop: Job,
        job_created_by_alice: Job,
    ) -> None:
        """Test that agents cannot download Final Payment POPs linked to multiple jobs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_final_payment_pop (Job): The job with a Final Payment POP.
            job_created_by_alice (Job): The job created by Alice.
        """
        trigger_multilinked_error(
            bob_agent_user_client,
            bob_job_with_final_payment_pop,
            job_created_by_alice,
            "final_payment_pop",
        )


class TestJobCompletionPhotoDownloadAccess:
    """Tests for permissions to download Job Completion Photos."""

    @staticmethod
    def test_manie_can_download(
        bob_job_with_manie_final_documentation: Job,
        manie_user_client: Client,
    ) -> None:
        """Test that Manie can download Job Completion Photos.

        Args:
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
            manie_user_client (Client): The Django test client for the Manie user.
        """
        job = bob_job_with_manie_final_documentation
        completion_photos = job.job_completion_photos.all()
        assert len(completion_photos) == BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS

        for completion_photo in completion_photos:
            response = manie_user_client.head(completion_photo.photo.url)
            assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_superuser_can_download(
        bob_job_with_manie_final_documentation: Job,
        superuser_client: Client,
    ) -> None:
        """Test that superusers can download Job Completion Photos.

        Args:
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
            superuser_client (Client): The Django test client for the superuser.
        """
        job = bob_job_with_manie_final_documentation
        completion_photos = job.job_completion_photos.all()
        assert len(completion_photos) == BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS

        for completion_photo in completion_photos:
            response = superuser_client.head(completion_photo.photo.url)
            assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_can_download(
        bob_agent_user_client: Client,
        bob_job_with_manie_final_documentation: Job,
    ) -> None:
        """Test that agents who created the job can download Job Completion Photos.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
        """
        job = bob_job_with_manie_final_documentation
        completion_photos = job.job_completion_photos.all()
        assert len(completion_photos) == BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS

        for completion_photo in completion_photos:
            response = bob_agent_user_client.head(completion_photo.photo.url)
            assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_other_agent_cannot_download(
        alice_agent_user_client: Client,
        bob_job_with_manie_final_documentation: Job,
    ) -> None:
        """Test that agents not creating the job cannot download Job Completion Photos.

        Args:
            alice_agent_user_client (Client): The Django test client for the Alice agent
                user.
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
        """
        job = bob_job_with_manie_final_documentation
        completion_photos = job.job_completion_photos.all()
        assert len(completion_photos) == BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS

        for completion_photo in completion_photos:
            response = alice_agent_user_client.head(completion_photo.photo.url)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_none_manie_none_agent_cannot_download(
        bob_job_with_manie_final_documentation: Job,
        bob_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that users not Manie or agents cannot download Job Completion Photos.

        Args:
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_agent_user (User): The Bob agent user.
        """
        bob_agent_user.is_agent = False
        bob_agent_user.save()

        job = bob_job_with_manie_final_documentation
        completion_photos = job.job_completion_photos.all()
        assert len(completion_photos) == BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS

        for completion_photo in completion_photos:
            response = bob_agent_user_client.head(completion_photo.photo.url)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_unlinked_file(
        bob_agent_user_client: Client,
    ) -> None:
        """Test that agents cannot download unlinked Job Completion Photos.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
        """
        response = bob_agent_user_client.head(
            "/private-media/completion_photos/test.jpg",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_multilinked_file(
        bob_agent_user_client: Client,
        bob_job_with_manie_final_documentation: Job,
        job_created_by_alice: Job,
    ) -> None:
        """Test that agents cannot download Job Completion Photos tied to multiple jobs.

        Args:
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
            job_created_by_alice (Job): The job created by Alice.
        """
        trigger_multilinked_error(
            bob_agent_user_client,
            bob_job_with_manie_final_documentation,
            job_created_by_alice,
            "job_completion_photo",
        )

    @staticmethod
    def test_agent_cannot_download_files_from_other_directories(
        bob_job_with_manie_final_documentation: Job,
        manie_user_client: Client,
    ) -> None:
        """Test that agents cannot download files from unknown directories.

        Args:
            bob_job_with_manie_final_documentation (Job): The job with Manies final
                documentation added to it.
            manie_user_client (Client): The Django test client for the Manie user.
        """
        completion_photo = check_type(
            bob_job_with_manie_final_documentation.job_completion_photos.first(),
            JobCompletionPhoto,
        )
        response = manie_user_client.get(
            completion_photo.photo.url.replace("completion_photos", "other"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_agent_cannot_download_images_with_unknown_extension(
        bob_job_with_manie_final_documentation: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Test that agents cannot download images with unknown extensions.

        Args:
            bob_job_with_manie_final_documentation (Job): The job with Manies
                final documentation added to it.
            bob_agent_user_client (Client): The Django test client for the Bob agent
                user.
        """
        completion_photo = check_type(
            bob_job_with_manie_final_documentation.job_completion_photos.first(),
            JobCompletionPhoto,
        )
        response = bob_agent_user_client.get(
            completion_photo.photo.url.replace(".jpg", ".pcx"),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
