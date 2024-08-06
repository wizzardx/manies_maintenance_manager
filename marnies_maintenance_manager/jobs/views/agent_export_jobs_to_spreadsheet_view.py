"""View for exporting jobs to a CSV file for a specific agent."""

import csv
import datetime
from copy import copy
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404
from django.http import HttpResponse
from django.template.defaultfilters import date as date_filter
from django.template.defaultfilters import yesno as yesno_filter
from django.utils import timezone
from typeguard import check_type

from marnies_maintenance_manager.jobs.constants import JOB_LIST_TABLE_COLUMN_NAMES
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.templatetags.custom_filters import (
    to_char as to_char_filter,
)
from marnies_maintenance_manager.users.models import User


def convert_job_to_rowdict(job: Job) -> dict[str, str]:
    """Convert a Job instance to a dictionary suitable for writing to a CSV file.

    Args:
        job (Job): The Job instance.

    Returns:
        dict[str, str]: The dictionary representation of the Job instance.
    """
    return {
        "Number": str(job.number),
        "Date": date_filter(job.date, "Y-m-d"),
        "Address Details": job.address_details,
        "Quote Request Details": job.quote_request_details,
        "Date of Inspection": date_filter(job.date_of_inspection, "Y-m-d"),
        "Accept or Reject A/R": to_char_filter(job.accepted_or_rejected),
        "Job Date": date_filter(job.job_onsite_work_completion_date, "Y-m-d"),
        "Comments on the job": job.comments,
        "Job Complete": check_type(yesno_filter(job.complete, "Yes,No"), str),
    }


def check_rowdict_has_expected_keys(
    rowdict: dict[str, str],
    expected_keys: list[str],
) -> None:
    """Check that the keys in the rowdict match the expected keys.

    Args:
        rowdict (dict[str, str]): The rowdict.
        expected_keys (list[str]): The expected keys.

    Raises:
        ValueError: If the keys in the rowdict do not match the expected keys.
    """
    if set(rowdict) != set(expected_keys):
        msg = (
            "Mismatch between headers and rowdict keys. "
            f"Found headers: {expected_keys}, rowdict keys: {set(rowdict.keys())}"
        )
        raise ValueError(msg)


def get_download_filename(agent_username: str, timestamp: datetime.datetime) -> str:
    """Get the filename for the CSV file to be downloaded.

    Args:
        agent_username (str): The username of the agent.
        timestamp (datetime.datetime): The timestamp.

    Returns:
        str: The filename.
    """
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"marnie_maintenance_jobs_for_{agent_username}_as_of_{timestamp_str}.csv"


def get_download_content_disposition(
    agent_username: str,
    timestamp: datetime.datetime,
) -> str:
    """Get the Content-Disposition header value for the CSV file to be downloaded.

    Args:
        agent_username (str): The username of the agent.
        timestamp (datetime.datetime): The timestamp.

    Returns:
        str: The Content-Disposition header value.
    """
    filename = get_download_filename(agent_username, timestamp)
    return f'inline; filename="{filename}"'


def get_initial_http_response(
    agent_username: str,
    timestamp: datetime.datetime,
    request: WSGIRequest,
) -> HttpResponse:
    """Get the initial HTTP response for the CSV file to be downloaded.

    Args:
        agent_username (str): The username of the agent.
        timestamp (datetime.datetime): The timestamp.
        request (WSGIRequest): The HTTP request.

    Returns:
        HttpResponse: The initial HTTP response.
    """
    filename = get_download_filename(agent_username, timestamp)

    # Option that can be added to the URL to view the CSV as text within
    # the browser, instead of downloading as a CSV file.
    inline_display_type = "inline"

    if request.GET.get("display") == inline_display_type:
        response = HttpResponse(content_type="text/plain; charset=utf-8")
        content_disposition = (
            f"inline; filename=\"{filename}\"; filename*=UTF-8''{filename}"
        )
    else:
        response = HttpResponse(content_type="text/csv")
        content_disposition = f'attachment; filename="{filename}"'

    response["Content-Disposition"] = content_disposition
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "no-cache"

    return response


def get_csv_file_headers() -> list[str]:
    """Get the headers for the CSV file.

    Returns:
        list[str]: The headers.
    """
    headers = copy(JOB_LIST_TABLE_COLUMN_NAMES)
    for unwanted in (
        "GPS Link",
        "Quote",
        "Deposit POP",
        "Photos",
        "Invoice",
        "Final Payment POP",
    ):
        headers.remove(unwanted)
    return headers


@login_required
def agent_export_jobs_to_spreadsheet_view(
    request: WSGIRequest,
    pk: UUID,
) -> HttpResponse:
    """Export the jobs for a specific agent to a CSV file.

    Args:
        request (WSGIRequest): The HTTP request.
        pk (UUID): The primary key of the User instance.

    Returns:
        HttpResponse: The HTTP response.

    Raises:
        PermissionDenied: If the user is not an agent.
        Http404: If there are no jobs for the agent.
    """
    user = check_type(request.user, User)  # type guard

    # For now only agents may access this view
    if not user.is_agent:
        raise PermissionDenied

    # This currently only works if the current user matches the uuid in the URL
    if user.id != pk:
        raise PermissionDenied

    # Get the jobs
    jobs = Job.objects.filter(agent=user)
    # An error if there are no jobs, as there is nothing to export
    if not jobs.exists():
        msg = "No jobs found for this agent."
        raise Http404(msg)

    # Set up the CSV file
    agent_username = user.username
    timestamp = timezone.now()
    response = get_initial_http_response(agent_username, timestamp, request)
    headers = get_csv_file_headers()

    writer = csv.DictWriter(response, fieldnames=headers)
    writer.writeheader()

    # Write the jobs to the CSV file
    for job in jobs:
        rowdict = convert_job_to_rowdict(job)
        check_rowdict_has_expected_keys(rowdict, headers)
        writer.writerow(rowdict)

    # Return the final response
    return response
