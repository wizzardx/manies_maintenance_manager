"""Tests for the agent_export_jobs_to_spreadsheet_view view."""

# pylint: disable=magic-value-comparison,disable=line-too-long
# ruff: noqa: E501

import datetime

import pytest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.views.agent_export_jobs_to_spreadsheet_view import (
    check_rowdict_has_expected_keys,
)
from manies_maintenance_manager.jobs.views.agent_export_jobs_to_spreadsheet_view import (
    convert_job_to_rowdict,
)
from manies_maintenance_manager.jobs.views.agent_export_jobs_to_spreadsheet_view import (
    get_csv_file_headers,
)
from manies_maintenance_manager.jobs.views.agent_export_jobs_to_spreadsheet_view import (
    get_download_content_disposition,
)
from manies_maintenance_manager.jobs.views.agent_export_jobs_to_spreadsheet_view import (
    get_download_filename,
)
from manies_maintenance_manager.jobs.views.agent_export_jobs_to_spreadsheet_view import (
    get_initial_http_response,
)
from manies_maintenance_manager.users.models import User


def test_convert_job_to_rowdict(bob_job_with_final_payment_pop: Job) -> None:
    """Test that the convert_job_to_rowdict function returns the correct rowdict.

    Args:
        bob_job_with_final_payment_pop (Job): The job instance.
    """
    rowdict = convert_job_to_rowdict(bob_job_with_final_payment_pop)
    assert rowdict == {
        "Accept or Reject A/R": "A",
        "Address Details": "1234 Main St, Springfield, IL",
        "Comments on the job": "Job completed successfully",
        "Date": "2022-01-01",
        "Date of Inspection": "2001-02-05",
        "Job Complete": "Yes",
        "Job Date": "2022-01-01",
        "Number": "1",
        "Quote Request Details": "Replace the kitchen sink",
    }


def test_rowdict_has_expected_keys_with_valid_expected_keys(
    bob_job_with_final_payment_pop: Job,
) -> None:
    """Test that the check_rowdict_has_expected_keys function works with valid expected keys.

    Args:
        bob_job_with_final_payment_pop (Job): The job instance.
    """
    rowdict = convert_job_to_rowdict(bob_job_with_final_payment_pop)
    expected_keys = [
        "Number",
        "Date",
        "Address Details",
        "Quote Request Details",
        "Date of Inspection",
        "Accept or Reject A/R",
        "Job Date",
        "Comments on the job",
        "Job Complete",
    ]
    check_rowdict_has_expected_keys(rowdict, expected_keys)


def test_rowdict_has_expected_keys_with_invalid_expected_keys(
    bob_job_with_final_payment_pop: Job,
) -> None:
    """Test check_rowdict_has_expected_keys raises ValueError for invalid keys.

    Args:
        bob_job_with_final_payment_pop (Job): The job instance.
    """
    rowdict = convert_job_to_rowdict(bob_job_with_final_payment_pop)
    expected_keys = [
        "Number",
        "Date",
        "Address Details",
        "Quote Request Details",
        "Date of Inspection",
        "Accept or Reject A/R",
        "Job Date",
        "Comments on the job",
        "Job Complete",
        "Extra Key",
    ]
    with pytest.raises(ValueError, match="Mismatch between headers and rowdict keys"):
        check_rowdict_has_expected_keys(rowdict, expected_keys)


def test_get_get_download_filename() -> None:
    """Test that the get_download_filename function returns the correct filename."""
    agent_username = "bob"
    timestamp = datetime.datetime(2022, 1, 2, 3, 4, 5, tzinfo=datetime.UTC)
    assert (
        get_download_filename(agent_username, timestamp)
        == "manie_maintenance_jobs_for_bob_as_of_20220102_030405.csv"
    )


def test_get_download_content_disposition_header() -> None:
    """Test that the get_download_content_disposition function returns the correct header."""
    agent_username = "bob"
    timestamp = datetime.datetime(2022, 1, 2, 3, 4, 5, tzinfo=datetime.UTC)
    assert get_download_content_disposition(agent_username, timestamp) == (
        'inline; filename="manie_maintenance_jobs_for_bob_as_of_20220102_030405.csv"'
    )


def test_get_initial_http_response_inline_display() -> None:
    """Test that the get_initial_http_response function works with an inline display parameter."""
    agent_username = "alice"
    timestamp = datetime.datetime(2023, 4, 5, 6, 7, 8, tzinfo=datetime.UTC)
    factory = RequestFactory()
    request = factory.get("/?display=inline")

    response = get_initial_http_response(agent_username, timestamp, request)

    assert isinstance(response, HttpResponse)
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert response["Content-Disposition"] == (
        'inline; filename="manie_maintenance_jobs_for_alice_as_of_'
        "20230405_060708.csv\"; filename*=UTF-8''manie_maintenance_"
        "jobs_for_alice_as_of_20230405_060708.csv"
    )
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Cache-Control"] == "no-cache"


def test_get_initial_http_response_non_inline_display() -> None:
    """Test get_initial_http_response with non-inline display parameter."""
    agent_username = "bob"
    timestamp = datetime.datetime(2023, 4, 5, 6, 7, 8, tzinfo=datetime.UTC)
    factory = RequestFactory()
    request = factory.get("/")

    response = get_initial_http_response(agent_username, timestamp, request)

    assert isinstance(response, HttpResponse)
    assert response["Content-Type"] == "text/csv"
    assert response["Content-Disposition"] == (
        'attachment; filename="manie_maintenance_jobs_for_bob_as_of_20230405_'
        '060708.csv"'
    )
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Cache-Control"] == "no-cache"


def test_get_initial_http_response_with_different_display_param() -> None:
    """Test that the get_initial_http_response function works with a different display parameter."""
    agent_username = "charlie"
    timestamp = datetime.datetime(2023, 4, 5, 6, 7, 8, tzinfo=datetime.UTC)
    factory = RequestFactory()
    request = factory.get("/?display=something_else")

    response = get_initial_http_response(agent_username, timestamp, request)

    assert isinstance(response, HttpResponse)
    assert response["Content-Type"] == "text/csv"
    assert response["Content-Disposition"] == (
        'attachment; filename="manie_maintenance_jobs_for_charlie_as_of_'
        '20230405_060708.csv"'
    )
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Cache-Control"] == "no-cache"


def test_get_csv_file_headers() -> None:
    """Test that the get_csv_file_headers function returns the correct headers."""
    headers = get_csv_file_headers()
    assert headers == [
        "Number",
        "Date",
        "Address Details",
        "Quote Request Details",
        "Date of Inspection",
        "Accept or Reject A/R",
        "Job Date",
        "Comments on the job",
        "Job Complete",
    ]


class TestAgentExportJobsToSpreadsheetView:
    """Tests for the agent_export_jobs_to_spreadsheet_view view."""

    @staticmethod
    def test_anon_user_is_redirected(bob_agent_user: User, client: Client) -> None:
        """Test that the view redirects to the login page when the user is anonymous.

        Args:
            bob_agent_user (User): The agent user.
            client (Client): The anonymous user's client.
        """
        url = reverse(
            "jobs:agent_export_jobs_to_spreadsheet_view",
            kwargs={"pk": bob_agent_user.pk},
        )
        response = check_type(client.get(url), HttpResponseRedirect)
        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == f"/accounts/login/?next={url}"

    @staticmethod
    def test_none_agent_is_denied(
        bob_agent_user: User,
        manie_user_client: Client,
    ) -> None:
        """Test that the view returns a 403 when the user is not an agent.

        Args:
            bob_agent_user (User): The agent user.
            manie_user_client (Client): The non-agent user's client.
        """
        url = reverse(
            "jobs:agent_export_jobs_to_spreadsheet_view",
            kwargs={"pk": bob_agent_user.pk},
        )
        response = manie_user_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_other_agent_is_denied(
        alice_agent_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test that the view returns a 403 when the user is not the agent.

        Args:
            alice_agent_user_client (Client): The agent user's client.
            bob_agent_user (User): The agent user.
        """
        url = reverse(
            "jobs:agent_export_jobs_to_spreadsheet_view",
            kwargs={"pk": bob_agent_user.pk},
        )
        response = alice_agent_user_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_fails_when_no_jobs_for_agent(
        bob_agent_user: User,
        bob_agent_user_client: Client,
    ) -> None:
        """Test that the view returns a 404 when there are no jobs for the agent.

        Args:
            bob_agent_user (User): The agent user.
            bob_agent_user_client (Client): The agent user's client.
        """
        url = reverse(
            "jobs:agent_export_jobs_to_spreadsheet_view",
            kwargs={"pk": bob_agent_user.pk},
        )
        response = bob_agent_user_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_succeeds_when_jobs_for_agent(
        bob_agent_user: User,
        bob_agent_user_client: Client,
        bob_job_with_final_payment_pop: Job,  # pylint: disable=unused-argument
    ) -> None:
        """Test that the view returns a CSV file with the correct headers and data.

        Args:
            bob_agent_user (User): The agent user.
            bob_agent_user_client (Client): The agent user's client.
            bob_job_with_final_payment_pop (Job): The job for the agent.
        """
        url = reverse(
            "jobs:agent_export_jobs_to_spreadsheet_view",
            kwargs={"pk": bob_agent_user.pk},
        )
        response = bob_agent_user_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert (
            'attachment; filename="manie_maintenance_jobs_for_bob_as_of_'
            in response["Content-Disposition"]
        )
        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["Cache-Control"] == "no-cache"
        assert (
            b"Number,Date,Address Details,Quote Request Details,Date of Inspection,"
            b"Accept or Reject A/R,Job Date,Comments on the job,Job Complete"
        ) in response.content
