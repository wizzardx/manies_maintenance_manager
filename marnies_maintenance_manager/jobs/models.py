"""Models for managing jobs in the Marnie's Maintenance Manager application."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import UUIDModel

from marnies_maintenance_manager.users.models import User


def _validate_user_is_agent(user_id: int) -> None:
    """Ensure the user is an agent."""
    user = User.objects.get(pk=user_id)
    if not user.is_agent:  # pragma: no branch
        raise ValidationError(
            _("%(values)s is not an Agent."),
            params={"values": user},
        )


class Job(UUIDModel):
    """
    Represents a maintenance job with all relevant details.

    Attributes:
        date (DateField): The date on which the job is scheduled.
        address_details (TextField): Description of the job location.
        gps_link (URLField): URL to the GPS coordinates of the job site.
        quote_request_details (TextField): Specifics of the maintenance request.
        agent(User): The Agent who initially created the maintenance job.
    """

    date = models.DateField()
    address_details = models.TextField()
    gps_link = models.URLField()
    quote_request_details = models.TextField()
    agent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        editable=False,
        validators=[_validate_user_is_agent],
    )
