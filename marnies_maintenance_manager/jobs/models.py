"""Models for managing jobs in the Marnie's Maintenance Manager application."""

import uuid
from enum import Enum
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from model_utils import Choices
from model_utils.fields import StatusField
from model_utils.models import TimeStampedModel
from model_utils.models import UUIDModel
from private_storage.fields import PrivateFileField
from private_storage.fields import PrivateImageField

from marnies_maintenance_manager.jobs.validators import validate_pdf_contents
from marnies_maintenance_manager.users.models import User


def validate_user_is_agent(user_id: uuid.UUID) -> None:
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
        agent(User): The Agent who initially created the maintenance job.j
        number (PositiveIntegerField): The unique-per-Agent number assigned to the job.
        date (DateField): The date on which the job is scheduled.
        address_details (TextField): Description of the job location.
        gps_link (URLField): URL to the GPS coordinates of the job site.
        quote_request_details (TextField): Specifics of the maintenance request.
    """

    # The fields below are populated initially when the Agent makes a new Maintenance
    # Job in the UI:
    agent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        editable=False,
        validators=[validate_user_is_agent],
    )
    number = models.PositiveIntegerField(editable=False)
    date = models.DateField()
    address_details = models.TextField()
    gps_link = models.URLField()
    quote_request_details = models.TextField()

    # As the job progresses, the status field is updated to reflect the current state.
    # This pattern of "STATUS" and "status" is the one presented by the
    # django-model-utils library. The 'status' field defaults to the first item in
    # the 'STATUS' object.

    # And Status is our own custom Enum that we use on top of that, to help create
    # some additional type safety.
    class Status(Enum):
        """Enum for the status of the job."""

        PENDING_INSPECTION = "pending_inspection"
        INSPECTION_COMPLETED = "inspection_completed"
        QUOTE_REJECTED_BY_AGENT = "quote_rejected_by_agent"
        QUOTE_ACCEPTED_BY_AGENT = "quote_accepted_by_agent"
        DEPOSIT_POP_UPLOADED = "deposit_pop_uploaded"
        MARNIE_COMPLETED = "marnie_completed"
        FINAL_PAYMENT_POP_UPLOADED = "final_payment_pop_uploaded"

    # STATUS is populated from the values seen in the Status Enum above.
    STATUS = Choices(  # type: ignore[no-untyped-call]
        (Status.PENDING_INSPECTION.value, _("Pending Inspection")),
        (Status.INSPECTION_COMPLETED.value, _("Inspection Completed")),
        (Status.QUOTE_REJECTED_BY_AGENT.value, _("Quote Rejected By Agent")),
        (Status.QUOTE_ACCEPTED_BY_AGENT.value, _("Quote Accepted By Agent")),
        (Status.DEPOSIT_POP_UPLOADED.value, _("Deposit POP Uploaded")),
        (Status.MARNIE_COMPLETED.value, _("Marnie has completed the job")),
        (
            Status.FINAL_PAYMENT_POP_UPLOADED.value,
            _("Agent uploaded the final payment POP"),
        ),
    )
    status = StatusField()  # type: ignore[no-untyped-call]

    # Marnie populates these fields in the UI later on, after doing the initial
    # requested on-site inspection. The Agent can then see the details of the quote
    date_of_inspection = models.DateField(null=True, blank=True)
    quote = PrivateFileField(
        upload_to="quotes/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["pdf"]), validate_pdf_contents],
    )

    # This field records whether Marnies quote was accepted or rejected by the
    # agent.
    class AcceptedOrRejected(Enum):
        """Enum for the acceptance status of the quote."""

        ACCEPTED = "accepted"
        REJECTED = "rejected"

    ACCEPTED_OR_REJECTED_CHOICES = [
        (AcceptedOrRejected.ACCEPTED.value, _("Accepted")),
        (AcceptedOrRejected.REJECTED.value, _("Rejected")),
    ]

    # This field is populated from the values seen in the AcceptedOrRejected Enum above.
    accepted_or_rejected = models.CharField(
        max_length=8,
        choices=ACCEPTED_OR_REJECTED_CHOICES,
        blank=True,
        default="",
    )

    deposit_proof_of_payment = PrivateFileField(
        upload_to="deposit_pops/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["pdf"]), validate_pdf_contents],
        help_text=_("Upload the deposit proof of payment here."),
        verbose_name=_("Deposit Proof of Payment"),
    )

    job_date = models.DateField(
        blank=True,
        null=True,
        help_text=_("Date when the job was completed."),
        verbose_name=_("Job Date"),
    )

    invoice = PrivateFileField(
        upload_to="invoices/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["pdf"]), validate_pdf_contents],
        help_text=_("Upload the invoice here."),
        verbose_name=_("Invoice"),
    )

    comments = models.TextField(
        default="",
        blank=True,
        help_text=_("Add any comments you have about the job here."),
        verbose_name=_("Comments"),
    )

    complete = models.BooleanField(
        default=False,
        verbose_name=_("Job Complete"),
        help_text=_("Has the job been completed?"),
    )

    final_payment_pop = PrivateFileField(
        upload_to="final_payment_pops/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(["pdf"]), validate_pdf_contents],
        help_text=_("Upload the final payment proof of payment here."),
        verbose_name=_("Final Payment Proof of Payment"),
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
                msg = "The 'agent' field must be set before saving the Job"
                raise ValueError(msg)

            # If it's the first job for an Agent, then the number should be 1,
            # otherwise it should be the next number in the sequence.
            if (
                last_job := Job.objects.filter(agent=self.agent)
                .order_by("number")
                .last()
            ):
                if last_job.number is None:  # pragma: no cover
                    # This sanity-checking code is not covered by tests because it's
                    # hard to set up the conditions for it to be triggered.
                    msg = "The 'number' field for the last job for this Agent is None"
                    raise ValueError(msg)
                self.number = last_job.number + 1
            else:
                self.number = 1

        # Call full_clean() to ensure that the model is validated before saving it:
        self.full_clean()

        # Now we can save the model:
        super().save(*args, **kwargs)  # type: ignore[no-untyped-call]


class JobCompletionPhoto(UUIDModel, TimeStampedModel):
    """Model representing a photo taken upon job completion."""

    job = models.ForeignKey(
        Job,
        related_name="job_completion_photos",
        on_delete=models.CASCADE,
    )
    photo = PrivateImageField(upload_to="completion_photos/", blank=False, null=False)

    def __str__(self) -> str:
        """Return a basic string representation of the photo.

        Returns:
            str: A string that represents the photo, containing the job number and the
                 date and time it was uploaded.
        """
        return (
            f"Photo for job {self.job.number} of agent {self.job.agent.username}"
            f", uploaded at {self.created}"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the JobCompletionPhoto instance to the database.

        Args:
            *args (Any): Additional positional arguments.
            **kwargs (Any): Additional keyword arguments.
        """
        # Call full_clean() to ensure that the model is validated before saving it:
        self.full_clean()

        # Now we can save the model:
        super().save(*args, **kwargs)  # type: ignore[no-untyped-call]
