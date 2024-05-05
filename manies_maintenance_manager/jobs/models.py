"""Models for managing jobs in the Manies Maintenance Manager application."""

from django.db import models
from model_utils.models import UUIDModel


class Job(UUIDModel):
    """
    Represents a maintenance job with all relevant details.

    Attributes:
        date (DateField): The date on which the job is scheduled.
        address_details (TextField): Description of the job location.
        gps_link (URLField): URL to the GPS coordinates of the job site.
        quote_request_details (TextField): Specifics of the maintenance request.
    """

    date = models.DateField()
    address_details = models.TextField()
    gps_link = models.URLField()
    quote_request_details = models.TextField()
