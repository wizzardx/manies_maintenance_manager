"""This module provides mixins for views in the Manie's Maintenance Manager project.

The `JobSuccessUrlMixin` class contains common functionality for generating
success URLs after form submissions in job-related views.
"""

# pylint: disable=too-few-public-methods

from typing import Protocol

from django.http import HttpRequest
from django.urls import reverse
from typeguard import check_type

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.users.models import User


class ViewProtocol(Protocol):
    """Protocol defining the interface for views using JobSuccessUrlMixin.

    Attributes:
        request (HttpRequest): The HTTP request object.

    Methods:
        get_object() -> Job: Method to retrieve the Job object associated with the view.
    """

    request: HttpRequest

    def get_object(self) -> Job:
        """Retrieve the Job object associated with the view."""


class JobSuccessUrlMixin:
    """Mixin providing a method to generate a success URL after form submission.

    This mixin assumes the presence of `request` and `get_object()` attributes/methods
    in the view that uses it.
    """

    def get_success_url(self: ViewProtocol) -> str:
        """Return the URL to redirect to after valid form submission.

        If the user is Manie, include the agent's username in the URL query parameters.

        Returns:
            str: The URL to redirect to after valid form submission.

        Raises:
            NotImplementedError: If reached by an unexpected user.
        """
        # We want to redirect to the job-listing page.

        # If we're the Manie user, then we also need to include an agent
        # username to be able to reach that listing correctly.

        # Who is the user behind the request?
        user = check_type(self.request.user, User)

        # Special logic if the user is Manie:
        if user.is_manie:
            # If the user is Manie, then we need to include the agent's
            # username in the URL.
            agent_username = self.get_object().agent.username
            return reverse("jobs:job_list") + f"?agent={agent_username}"

        # Check if we're another user, but we still reach this point.
        # It shouldn't happen in the current iteration of the code, but it will
        # happen later during dev. For now, raise a NotImplementedError.
        msg = "This logic should not be reached"  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover
