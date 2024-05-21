"""Models for managing jobs in the Marnie's Maintenance Manager application."""

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel

from marnies_maintenance_manager.users.models import User


def _validate_user_is_agent(user_id: uuid.UUID) -> None:
    """Ensure the user is an agent.

    Args:
        user_id (uuid.UUID): The unique identifier of the user to validate.

    Raises:
        ValidationError: If the specified user is not an agent.
    """
    user = User.objects.get(pk=user_id)
    if not user.is_agent:  # pragma: no branch
        raise ValidationError(
            _("%(values)s is not an Agent."),
            params={"values": user},
        )


class Job(UUIDModel, TimeStampedModel):
    """Represents a maintenance job with all relevant details.

    Attributes:
        number (PositiveIntegerField): The unique-per-Agent number assigned to the job.
        date (DateField): The date on which the job is scheduled.
        address_details (TextField): Description of the job location.
        gps_link (URLField): URL to the GPS coordinates of the job site.
        quote_request_details (TextField): Specifics of the maintenance request.
        agent(User): The Agent who initially created the maintenance job.
    """

    number = models.PositiveIntegerField(editable=False)
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

    class Meta:
        """Meta options for the Job model."""

        ordering = ["created"]
        unique_together = ["agent", "number"]

    def __str__(self) -> str:
        """Return a basic string representation of the job.

        Returns:
            str: A string that represents the job, containing the date and a shortened
                 version of the address with newlines replaced by spaces.
        """
        shortened_address = self.address_details[:50].replace("\n", " ")
        return f"{self.date}: {shortened_address}"

    def get_absolute_url(self) -> str:
        """Get URL for the job's detail view.

        Returns:
            str: URL for the job detail.
        """
        return reverse("jobs:job_detail", kwargs={"pk": self.pk})

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the job to the database.

        Args:
            *args (Any): Additional positional arguments.
            **kwargs (Any): Additional keyword arguments.

        Raises:
            ValueError: If the 'agent' field is not set before saving the job.
            ValueError: If the 'number' field for the last job for this Agent is None.
        """
        # Autopopulate the 'number' field correctly if it is not already set:
        if self.number is None:
            # The next part requires the 'agent' field to be set correctly, so
            # have an error check for it here:
            if self.agent is None:  # pragma: no cover
                # This sanity-checking code is not covered by tests because it's hard
                # to set up the conditions for it to be triggered.
                msg = "The 'agent' field must be set before saving the Job."
                raise ValueError(msg)

            # If it's the first job for an Agent then the number should be 1, otherwise
            # it should be the next number in the sequence.
            if (
                last_job := Job.objects.filter(agent=self.agent)
                .order_by("number")
                .last()
            ):
                if last_job.number is None:  # pragma: no cover
                    # This sanity-checking code is not covered by tests because it's
                    # hard to set up the conditions for it to be triggered.
                    msg = "The 'number' field for the last job for this Agent is None."
                    raise ValueError(msg)
                self.number = last_job.number + 1
            else:
                self.number = 1
        super().save(*args, **kwargs)  # type: ignore[no-untyped-call]
