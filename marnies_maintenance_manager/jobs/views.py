"""
View functions for the jobs module in the Marnie's Maintenance Manager application.

This module contains view functions that handle requests for listing maintenance jobs
and creating new maintenance jobs. Each view function renders an HTML template that
corresponds to its specific functionality.
"""

import logging
from typing import Any
from typing import cast

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseBase
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from marnies_maintenance_manager.users.models import User

from .constants import DEFAULT_FROM_EMAIL
from .exceptions import MarnieUserNotFoundError
from .models import Job
from .utils import count_admin_users
from .utils import count_agent_users
from .utils import count_marnie_users
from .utils import get_marnie_email
from .utils import get_sysadmin_email

logger = logging.getLogger(__name__)


USER_COUNT_PROBLEM_MESSAGES = {
    "NO_ADMIN_USERS": "WARNING: There are no Admin users.",
    "MANY_ADMIN_USERS": "WARNING: There are multiple Admin users.",
    "NO_MARNIE_USERS": "WARNING: There are no Marnie users.",
    "MANY_MARNIE_USERS": "WARNING: There are multiple Marnie users.",
    "NO_AGENT_USERS": "WARNING: There are no Agent users.",
}


class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):  # type: ignore[type-arg]
    """
    Display a list of all Maintenance Jobs.

    This view extends Django's ListView class to display a list of all maintenance jobs
    in the system. It uses the 'jobs/job_list.html' template.
    """

    model = Job
    template_name = "jobs/job_list.html"

    def test_func(self) -> bool:
        """Check if the user is an agent, or Marnie, or a superuser."""
        user = cast(User, self.request.user)
        return user.is_agent or user.is_superuser or user.is_marnie

    def dispatch(
        self,
        request: HttpRequest,
        *args: int,
        **kwargs: int,
    ) -> HttpResponseBase:
        """Handle exceptions in dispatch and provide appropriate responses.

        Enhances the default dispatch method by catching ValueError exceptions
        and returning a bad request response with the error message.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

    def get_queryset(self) -> QuerySet[Job]:
        """Filter Job instances by user's role and optional query parameters.

        Customizes the queryset based on user type. Marnie or superusers can filter
        jobs by agent. Agents see only their jobs. Raises ValueError if conditions
        are not met or parameters are missing.
        """
        user = cast(User, self.request.user)

        if user.is_marnie:
            agent_username = self.request.GET.get("agent")
            if not agent_username:
                msg = "Agent username parameter is missing"
                raise ValueError(msg)
            try:
                agent = User.objects.get(username=agent_username)
                return Job.objects.filter(agent=agent)
            except User.DoesNotExist as err:
                msg = "Agent username not found"
                raise ValueError(msg) from err
        elif user.is_agent:
            # For agents, we return all jobs that they initially created
            return Job.objects.filter(agent=user)
        elif user.is_superuser:  # pragma: no branch
            agent_username = self.request.GET.get("agent")
            if not agent_username:
                # Agent username parameter not provided, so for superuser, return all
                # jobs.
                return Job.objects.all()
            try:
                agent = User.objects.get(username=agent_username)
                return Job.objects.filter(agent=agent)
            except User.DoesNotExist as err:
                msg = "Agent username not found"
                raise ValueError(msg) from err

        else:  # pragma: no cover
            # There's no known use cases past this point (they should have been caught
            # in various other logic branches before logic reaches this point), but
            # just in case we do somehow reach this point, raise an error:
            msg = "Unknown user type"
            raise ValueError(msg)


class JobCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):  # type: ignore[type-arg]
    """
    Provide a form to create a new Maintenance Job.

    This view extends Django's CreateView class to create a form for users to input
    details for a new maintenance job. It uses the 'jobs/job_create.html' template.
    """

    model = Job
    fields = ["date", "address_details", "gps_link", "quote_request_details"]
    template_name = "jobs/job_create.html"
    success_url = reverse_lazy("jobs:job_list")

    def get_form(self, form_class: type[Any] | None = None) -> Any:
        """Modify the widgets of the form, to use HTML5 date input."""
        form = super().get_form(form_class)
        form.fields["date"].widget = forms.DateInput(attrs={"type": "date"})
        return form

    def form_valid(self, form: Any) -> HttpResponse:
        """Set the agent field to the current user before saving the form."""
        # The "form" is dynamically generated by Django, so we can't type-check it.

        # Sanity check that the user is logged in and that they are an Agent. All of
        # that should already be setup before the logic gets here, but just in case:

        if not self.request.user.is_authenticated:  # pragma: no cover
            msg = "User is not authenticated."
            raise ValueError(msg)

        if not self.request.user.is_agent:  # pragma: no cover
            msg = "User is not an agent."
            raise ValueError(msg)

        # Make sure that the "agent" field is set to the current user, before we
        # save to the database.
        form.instance.agent = self.request.user

        # Call validations/etc on parent classes
        response = super().form_valid(form)

        # Send an email notification
        job = self.object  # This is the Job object that has just been created and saved

        # Sanity check that we actually have a job:
        if not job:  # pragma: no cover
            msg = "Job object is missing."
            raise ValueError(msg)

        email_subject = f"New maintenance request by {job.agent.username}"

        email_body = (
            f"{job.agent.username} has made a new maintenance request.\n\n"
            f"Date: {job.date}\n\n"
            f"Address Details:\n\n{job.address_details}\n\n"
            f"GPS Link:\n\n{job.gps_link}\n\n"
            f"Quote Request Details:\n\n{job.quote_request_details}\n\n"
            f"PS: This mail is sent from an unmonitored email address. "
            "Please do not reply to this email.\n\n"
        )

        email_from = DEFAULT_FROM_EMAIL
        email_cc = self.request.user.email

        # One main error that can happen here is if the Marnie user account does
        # not exist.
        try:
            email_to = get_marnie_email()
        except MarnieUserNotFoundError:
            # Log the message here, then send a flash message to the user (it
            # will appear on their next web page). We don't raise an exception
            # further than this point.
            logger.exception(
                "No Marnie user found. Unable to send maintenance request email.",
            )
            messages.error(
                self.request,
                "No Marnie user found.\nUnable to send maintenance request.\n"
                "Please contact the system administrator at " + get_sysadmin_email(),
            )
        else:
            # Marnie's user account was found, so we can send the email:
            email = EmailMessage(
                subject=email_subject,
                body=email_body,
                from_email=email_from,
                to=[email_to],
                cc=[email_cc],
            )
            email.send()

            # And send the success flash message to the user:
            messages.success(
                self.request,
                "Your maintenance request has been sent to Marnie.",
            )

        return response

    def test_func(self) -> bool:
        """Check if the user is an agent, or a superuser."""
        user = cast(User, self.request.user)
        return user.is_agent or user.is_superuser


class _UserInfo:
    """Class to provide information about the users in the system."""

    @staticmethod
    def has_no_admin_users() -> bool:
        """Check if there are no superusers."""
        return count_admin_users() == 0

    @staticmethod
    def has_many_admin_users() -> bool:
        """Check if there are more than one superusers."""
        return count_admin_users() > 1

    @staticmethod
    def has_no_marnie_users() -> bool:
        """Check if there are no Marnie users."""
        return count_marnie_users() == 0

    @staticmethod
    def has_many_marnie_users() -> bool:
        """Check if there are more than one Marnie users."""
        return count_marnie_users() > 1

    @staticmethod
    def has_no_agent_users() -> bool:
        """Check if there are no agent users."""
        return count_agent_users() == 0


def home_page(request: HttpRequest) -> HttpResponse:
    """Render the home page for the application."""
    context = {
        "userinfo": _UserInfo,
        "warnings": USER_COUNT_PROBLEM_MESSAGES,
    }
    return render(request, "pages/home.html", context)
