"""User models for Manies Maintenance Manager.

This module extends the default Django user model to accommodate additional
fields and functionality specific to the needs of the Manies Maintenance Manager
application. The user model includes custom fields to handle various user roles
and permissions within the system.
"""

from django.contrib.auth.models import AbstractUser
from django.db.models import BooleanField
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for Manies Maintenance Manager.

    If adding fields that need to be filled at user signup, check forms.SignupForm
    and forms.SocialSignupForms accordingly.

    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    # If this is set to True, it means that this is an "Agent" user, ie the
    # user is someone from one of the property companies that Marnie works with, who
    # can create new Maintenance Jobs.
    is_agent = BooleanField(default=False)

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
