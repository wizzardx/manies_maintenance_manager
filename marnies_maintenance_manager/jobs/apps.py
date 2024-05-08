"""Define configuration for the jobs application in Django."""

from django.apps import AppConfig


class JobsConfig(AppConfig):
    """Configure settings and attributes for the jobs application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "marnies_maintenance_manager.jobs"
