"""A handler for when an agent accepts a quote for a Maintenance Job."""

from uuid import UUID

from django.http import HttpRequest
from django.http import HttpResponse
from rest_framework import status


def quote_accept(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Accept the quote for a specific Maintenance Job.

    Args:
        request (HttpRequest): The HTTP request.
        pk (UUID): The primary key of the Job instance.

    Returns:
        HttpResponse: The HTTP response.
    """
    msg = (
        f"This view is not implemented yet. Called with HTTP method "
        f"{request.method} and pk: {pk}"
    )
    return HttpResponse(msg, status=status.HTTP_501_NOT_IMPLEMENTED)
