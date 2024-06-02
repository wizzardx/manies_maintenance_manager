"""Tests for the accept_quote view."""

# pylint: disable=magic-value-comparison

from uuid import UUID

from django.test import RequestFactory
from rest_framework import status

from marnies_maintenance_manager.jobs.views.accept_quote_view import accept_quote


def test_does_nothing_because_not_yet_implemented() -> None:
    """Test that the view does nothing because it is not yet implemented."""
    # Assign job_id to a UUID:
    job_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    # Assign request to a RequestFactory instance:
    request = RequestFactory().post("/jobs/123/accept_quote")
    # Call the view function:
    response = accept_quote(request, job_id)
    # Assert that the response content is as expected:
    assert response.content.decode() == (
        "This view is not implemented yet. Called "
        "with HTTP method POST and pk: "
        "123e4567-e89b-12d3-a456-426614174000"
    )
    # Assert that the response status code is as expected:
    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
