"""A handler for when an agent accepts a quote for a Maintenance Job."""

from uuid import UUID

from django.http import HttpRequest
from django.http import HttpResponse


def accept_quote(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Accept the quote for a specific Maintenance Job.

    Args:
        request (HttpRequest): The HTTP request.
        pk (UUID): The primary key of the Job instance.

    Raises:
        NotImplementedError: If the view is not implemented yet.
    """
    msg = "This view is not implemented yet."
    raise NotImplementedError(msg)
