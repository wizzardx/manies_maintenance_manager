"""Provide a view to create a new Maintenance Job."""

from pathlib import Path
from typing import cast
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

GET_METHOD_NAME = "GET"


@login_required
def download_quote(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Download the quote for a specific Maintenance Job.

    Args:
        request (HttpRequest): The HTTP request.
        pk (UUID): The primary key of the Job instance.

    Returns:
        HttpResponse: The HTTP response.
    """
    # Return an http response where the user will get the pdf file as a download

    # Fail for none-GET request:
    if request.method != GET_METHOD_NAME:
        return HttpResponse(
            "Method not allowed",
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # Try to get the Job instance.
    try:
        job = Job.objects.get(pk=pk)
    except Job.DoesNotExist:
        return HttpResponse("Job not found", status=status.HTTP_404_NOT_FOUND)

    # Check if the Job instance has a quote.
    if not job.quote:
        return HttpResponse("Quote not set for job", status=status.HTTP_404_NOT_FOUND)

    # Only Marnie, Admin, and the agent who created this Job may access this view.
    user = cast(User, request.user)
    if not (
        user.is_marnie or user.is_superuser or (user.is_agent and user == job.agent)
    ):
        return HttpResponse("Access denied", status=status.HTTP_403_FORBIDDEN)

    quote_path = Path(job.quote.name)

    file_content = job.quote.read()
    content_type = "application/pdf"
    file_name = quote_path.name
    response = HttpResponse(file_content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    return response
