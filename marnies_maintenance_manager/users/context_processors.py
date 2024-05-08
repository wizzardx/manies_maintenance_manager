"""Provide context processors for user-related settings."""

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from typeguard import typechecked


@typechecked
def allauth_settings(request: WSGIRequest) -> dict[str, bool]:
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }
