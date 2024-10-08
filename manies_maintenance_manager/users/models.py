"""User models for Manie's Maintenance Manager.

This module extends the default Django user model to accommodate additional
fields and functionality specific to the needs of the Manie's Maintenance Manager
application. The user model includes custom fields to handle various user roles
and permissions within the system.
"""

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models import BooleanField
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils.models import UUIDModel


class User(AbstractUser, UUIDModel):
    """Ensure that an Agent user can only exist if Manie exists.

    Validates that if the user has the 'is_agent' flag set to True,
    a user designated as 'Manie' must also exist within the system.
    If this condition is not met, a ValidationError is raised.

    Returns:
        dict: A dictionary containing the cleaned (normalized) data.

    Raises:
        ValidationError: If 'is_agent' is True and no Manie user exists.
    """

    # First and last names do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    # If this is set to True, it means that this is an "Agent" user, i.e., the
    # user is someone from one of the property companies that Manie works with, who
    # can create new Maintenance Jobs.
    is_agent = BooleanField(
        _("User is an Agent"),
        default=False,
        help_text=_("Designates whether the user is an Agent."),
    )

    # If this is set to True, it means that this is Manie's user.
    is_manie = BooleanField(
        _("User is Manie"),
        default=False,
        help_text=_("Designates whether this user is Manie Ferreira."),
    )

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def clean(self) -> None:
        """Ensure that an Agent user can only exist if Manie exists.

        Validates that if the user has the 'is_agent' flag set to True,
        a user designated as 'Manie' must also exist within the system.
        If this condition is not met, a ValidationError is raised.

        Returns:
            dict: A dictionary containing the cleaned (normalized) data.

        Raises:
            ValidationError: If 'is_agent' is True and no Manie user exists.
        """
        cleaned_data = super().clean()  # pylint: disable=assignment-from-no-return

        # If is_agent is set to True, then ensure that a Manie user exists on the
        # system.
        if self.is_agent and not User.objects.filter(is_manie=True).exists():
            raise ValidationError(
                _("An Agent user can only exist if Manie exists."),
            )

        return cleaned_data
