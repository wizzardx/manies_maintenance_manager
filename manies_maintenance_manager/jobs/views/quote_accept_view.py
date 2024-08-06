"""A handler for when an agent accepts a quote for a Maintenance Job."""

from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse

from manies_maintenance_manager.jobs.utils import quote_accept_or_reject


@login_required
def quote_accept(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Accept the quote for a specific Maintenance Job.

    Args:
        request (HttpRequest): The HTTP request.
        pk (UUID): The primary key of the Job instance.

    Returns:
        HttpResponse: The HTTP response.
    """
    return quote_accept_or_reject(request, pk, accepted=True)
