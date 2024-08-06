"""Configure the "users" application within the Django project."""

import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    """Define configuration parameters for the "users" app."""

    name = "manies_maintenance_manager.users"
    verbose_name = _("Users")

    def ready(self) -> None:
        """Handle startup logic for the "users" app, including signal imports."""
        with contextlib.suppress(ImportError):
            # pylint: disable=import-outside-toplevel,no-name-in-module,unused-import
            import manies_maintenance_manager.users.signals  # noqa: F401
