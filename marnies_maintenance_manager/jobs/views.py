"""View functions for the jobs module in the Marnie's Maintenance Manager application.

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
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from zen_queries import fetch

from marnies_maintenance_manager.users.models import User

from .constants import DEFAULT_FROM_EMAIL
from .exceptions import MarnieUserNotFoundError
from .models import Job
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

USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES = {
    "NO_EMAIL_ADDRESS": "WARNING: User {username} has no email address.",
    "NO_VERIFIED_EMAIL_ADDRESS": (
        "WARNING: User {username} has not verified their email address."
    ),
    "NO_PRIMARY_EMAIL_ADDRESS": (
        "WARNING: User {username} has no primary email address."
    ),
    "EMAIL_MISMATCH": (
        "WARNING: User {username}'s email address does not match the verified "
        "primary email address."
    ),
}


# pylint: disable=too-many-ancestors
class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):  # type: ignore[type-arg]
    """Display a list of all Maintenance Jobs.

    This view extends Django's ListView class to display a list of all maintenance jobs
    in the system. It uses the 'jobs/job_list.html' template.
    """

    model = Job
    template_name = "jobs/job_list.html"

    def test_func(self) -> bool:
        """Check if the user is an agent, or Marnie, or a superuser.

        Returns:
            bool: True if the user has the required permissions, False otherwise.
        """
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

        Args:
            request (HttpRequest): The HTTP request.
            *args (int): Additional positional arguments.
            **kwargs (int): Additional keyword arguments.

        Returns:
            HttpResponseBase: The HTTP response.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

    def get_queryset(self) -> QuerySet[Job]:
        """Filter Job instances by user's role and optional query parameters.

        Returns:
            QuerySet[Job]: The queryset of Job instances.

        Raises:
            ValueError: If conditions are not met or parameters are missing.
        """
        user = cast(User, self.request.user)

        if user.is_marnie:
            agent_username = self.request.GET.get("agent")
            if not agent_username:  # pylint: disable=consider-using-assignment-expr
                msg = "Agent username parameter is missing"
                raise ValueError(msg)
            try:
                agent = User.objects.get(username=agent_username)
            except User.DoesNotExist as err:
                msg = "Agent username not found"
                raise ValueError(msg) from err
            return Job.objects.filter(agent=agent)

        if user.is_agent:
            # For agents, we return all jobs that they initially created
            return Job.objects.filter(agent=user)

        if user.is_superuser:  # pragma: no branch
            if not (agent_username := self.request.GET.get("agent")):
                # Agent username parameter not provided, so for superuser, return all
                # jobs.
                return Job.objects.all()
            try:
                agent = User.objects.get(username=agent_username)
            except User.DoesNotExist as err:
                msg = "Agent username not found"
                raise ValueError(msg) from err
            return Job.objects.filter(agent=agent)

        # There's no known use cases past this point (they should have been caught
        # in various other logic branches before logic reaches this point), but
        # just in case we do somehow reach this point, raise an error:
        msg = "Unknown user type"  # pragma: no cover
        raise ValueError(msg)  # pragma: no cover

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add additional context data to the template.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            dict[str, Any]: The context data.
        """
        context = super().get_context_data(**kwargs)

        # Present a different title to the template if "agent" is in the
        # query parameters.
        if agent_username := self.request.GET.get("agent"):
            context["title"] = f"Maintenance Jobs for {agent_username}"
        else:
            context["title"] = "Maintenance Jobs"
        return context


def _generate_email_body(job: Job) -> str:
    """Generate the email body for the maintenance request email.

    Args:
        job (Job): The Job object.

    Returns:
        str: The email body.
    """
    return (
        f"{job.agent.username} has made a new maintenance request.\n\n"
        f"Date: {job.date}\n\n"
        f"Address Details:\n\n{job.address_details}\n\n"
        f"GPS Link:\n\n{job.gps_link}\n\n"
        f"Quote Request Details:\n\n{job.quote_request_details}\n\n"
        f"PS: This mail is sent from an unmonitored email address. "
        "Please do not reply to this email.\n\n"
    )


def _user_has_verified_email_address(user: User) -> bool:
    """Check if the user has a verified email address.

    Args:
        user (User): The user.

    Returns:
        bool: True if the user has a verified email address, False otherwise.
    """
    return any(
        emailaddress.verified
        for emailaddress in user.emailaddress_set.all()  # type: ignore[attr-defined]
    )


def _user_has_primary_email_address(user: User) -> bool:
    """Check if the user has a primary email address.

    Args:
        user (User): The user.

    Returns:
        bool: True if the user has a primary email address, False otherwise.
    """
    return any(
        emailaddress.primary
        for emailaddress in user.emailaddress_set.all()  # type: ignore[attr-defined]
    )


def _marnie_has_verified_email_address(marnie_email: str) -> bool:
    """Check if Marnie has a verified email address.

    Args:
        marnie_email (str): The email address for Marnie.

    Returns:
        bool: True if Marnie has a verified email address, False otherwise.
    """
    return cast(
        bool,
        User.objects.get(email=marnie_email)
        .emailaddress_set.filter(  # type: ignore[attr-defined]
            verified=True,
        )
        .exists(),
    )


def _log_exception_and_flash_for_marnie_user_not_found(request: HttpRequest) -> None:
    """Log an exception and send a flash message for a Marnie user not found.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.exception(
        "No Marnie user found. Unable to send maintenance request email.",
    )
    messages.error(
        request,
        "No Marnie user found.\nUnable to send maintenance request email.\n"
        "Please contact the system administrator at " + get_sysadmin_email(),
    )


def _log_error_and_flash_for_user_no_email_address(request: HttpRequest) -> None:
    """Log an error and send a flash message for a user with no email address.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.error(
        "User %s has no email address. Unable to send maintenance request email.",
        request.user.username,
    )
    messages.error(
        request,
        "Your email address is missing.\nUnable to send maintenance "
        "request email.\nPlease contact the system administrator at "
        + get_sysadmin_email(),
    )


def _log_error_and_flash_for_user_no_verified_email_address(
    request: HttpRequest,
) -> None:
    """Log an error and send a flash message for a user with no verified email address.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.error(
        "User %s has not verified their email address. Unable to send"
        " maintenance request email.",
        request.user.username,
    )
    messages.error(
        request,
        "Your email address is not verified.\nUnable to send maintenance "
        "request email.\nPlease verify your email address and try again.",
    )


def _log_error_and_flash_for_marnie_user_no_email_address(request: HttpRequest) -> None:
    """Log an error and send a flash message for a Marnie user with no email address.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.error(
        "User marnie has no email address. Unable to send maintenance request email.",
    )
    messages.error(
        request,
        "Marnie's email address is missing.\nUnable to send maintenance "
        "request email.\nPlease contact the system administrator at "
        + get_sysadmin_email(),
    )


def _log_error_and_flash_for_marnie_user_no_verified_email_address(
    request: HttpRequest,
) -> None:
    """Log error and send a flash message for a Marnie user with no verified email.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.error(
        "Marnie's email address is not verified. "
        "Unable to send maintenance request email.",
    )
    messages.error(
        request,
        "Marnie's email address is not verified.\nUnable to send maintenance "
        "request email.\nPlease contact the system administrator at "
        + get_sysadmin_email(),
    )


class JobCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):  # type: ignore[type-arg]
    """Provide a form to create a new Maintenance Job.

    This view extends Django's CreateView class to create a form for users to input
    details for a new maintenance job. It uses the 'jobs/job_create.html' template.
    """

    model = Job
    fields = ["date", "address_details", "gps_link", "quote_request_details"]
    template_name = "jobs/job_create.html"
    success_url = reverse_lazy("jobs:job_list")

    def get_form(self, form_class: type[Any] | None = None) -> Any:
        """Modify the widgets of the form, to use HTML5 date input.

        Args:
            form_class (type[Any], optional): The form class. Defaults to None.

        Returns:
            Any: The form instance.
        """
        form = super().get_form(form_class)
        form.fields["date"].widget = forms.DateInput(attrs={"type": "date"})
        return form

    def form_valid(self, form: Any) -> HttpResponse:
        """Set the agent field to the current user before saving the form.

        Args:
            form (Any): The form instance.

        Returns:
            HttpResponse: The HTTP response.

        Raises:
            ValueError: If the user is not authenticated or not an agent, or if the
                job object is missing.
        """
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
        # Over here, `job` is the JOb object that has just been created and saved.
        if not (job := self.object):  # pragma: no cover
            msg = "Job object is missing."
            raise ValueError(msg)

        email_subject = f"New maintenance request by {job.agent.username}"

        email_body = _generate_email_body(job)

        email_from = DEFAULT_FROM_EMAIL
        email_cc = self.request.user.email

        # One main error that can happen here is if the Marnie user account does
        # not exist.
        try:
            marnie_email = get_marnie_email()
        except MarnieUserNotFoundError:
            # Log the message here, then send a flash message to the user (it
            # will appear on their next web page). We don't raise an exception
            # further than this point.
            _log_exception_and_flash_for_marnie_user_not_found(
                self.request,
            )
            return response

        # Marnie's user account was found. Next, check the user's own email address
        # to see if it's valid. If it's not, we can't send the email.
        if not self.request.user.email:
            # The user's email address is missing. Log the message, then send a
            # flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_user_no_email_address(self.request)
            return response

        # Users email address was found. Check if Marnie user has an email address.
        if not marnie_email:
            # The Marnie user's email address is missing. Log the message, then send
            # a flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_marnie_user_no_email_address(self.request)
            return response

        # Check if the agent user has a verified email address
        if not _user_has_verified_email_address(self.request.user):
            # The user's email address is not verified. Log the message, then send a
            # flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_user_no_verified_email_address(self.request)
            return response

        # Check if Marnie has a verified email address
        if not _marnie_has_verified_email_address(marnie_email=marnie_email):
            # Marnies email address is not verified. Log the message, then send a
            # flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_marnie_user_no_verified_email_address(self.request)
            return response

        # Marnie's user account and other required details were found, so we can
        # send the email:
        email_to = get_marnie_email()

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
        """Check if the user is an agent, or Marnie, or a superuser.

        Returns:
            bool: True if the user has the required permissions, False otherwise.
        """
        user = cast(User, self.request.user)
        return user.is_agent or user.is_superuser


class UserInfo:
    """Class to efficiently provide information about the users to Templates.

    One reason we use this is to avoid a very large amount of user-related querying
    when rendering the home page jor users. Instead, we instantiate this object once
    pass it as a template context variable to the home page view, and in there
    it uses its internal cache or calculates details without repeatedly querying
    the db in a horrible set of N+1 patterns.
    """

    def __init__(self) -> None:
        """Initialize the UserInfo object."""
        self._cached_users = fetch(
            User.objects.all().prefetch_related(
                "emailaddress_set",
            ),
        )
        self._user_emails = {
            user.id: list(user.emailaddress_set.all()) for user in self._cached_users
        }

    def count_admin_users(self) -> int:
        """Return the number of superusers.

        Returns:
            int: The number of superusers.
        """
        return sum(user.is_superuser for user in self._cached_users)

    def count_marnie_users(self) -> int:
        """Return the number of Marnie users.

        Returns:
            int: The number of Marnie users.
        """
        return sum(user.is_marnie for user in self._cached_users)

    def count_agent_users(self) -> int:
        """Return the number of Agent users.

        Returns:
            int: The number of Agent users.
        """
        return sum(user.is_agent for user in self._cached_users)

    def has_no_admin_users(self) -> bool:
        """Check if there are no superusers.

        Returns:
            bool: True if there are no superusers, False otherwise.
        """
        return self.count_admin_users() == 0

    def has_many_admin_users(self) -> bool:
        """Check if there are more than one superusers.

        Returns:
            bool: True if there are more than one superusers, False otherwise.
        """
        return self.count_admin_users() > 1

    def has_no_marnie_users(self) -> bool:
        """Check if there are no Marnie users.

        Returns:
            bool: True if there are no Marnie users, False otherwise.
        """
        return self.count_marnie_users() == 0

    def has_many_marnie_users(self) -> bool:
        """Check if there are more than one Marnie users.

        Returns:
            bool: True if there are more than one Marnie users, False otherwise.
        """
        return self.count_marnie_users() > 1

    def has_no_agent_users(self) -> bool:
        """Check if there are no agent users.

        Returns:
            bool: True if there are no agent users, False otherwise.
        """
        return self.count_agent_users() == 0

    def users_with_no_verified_email_address(self) -> list[User]:
        """Get all users with no verified email address.

        Returns:
            list[User]: A list of all users with no verified email address.
        """
        return [
            user
            for user in self._cached_users
            if not _user_has_verified_email_address(user)
        ]

    def users_with_no_primary_email_address(self) -> list[User]:
        """Get all users with no primary email address.

        Returns:
            list[User]: A list of all users with no primary email address.
        """
        return [
            user
            for user in self._cached_users
            if not _user_has_primary_email_address(user)
        ]

    def users_with_primary_verified_email_mismatch(self) -> list[User]:
        """Get all users with a mismatch between primary and verified email addresses.

        Returns:
            list[User]: A list of all users with a mismatch between primary and
                        verified email addresses.
        """
        mismatched_users = []

        for user in self._cached_users:
            primary_email_found = False
            verified_primary_email = False
            primary_email_matches = False

            for emailaddress in self._user_emails[user.id]:
                if emailaddress.primary:
                    primary_email_found = True
                    if emailaddress.verified:
                        verified_primary_email = True
                    if emailaddress.email == user.email:
                        primary_email_matches = True

            if primary_email_found and (
                not verified_primary_email or not primary_email_matches
            ):
                mismatched_users.append(user)

        return mismatched_users

    def users_with_no_email_address(self) -> list[User]:
        """Get all users with no email address.

        Returns:
            list[User]: A list of all users with no email address.
        """
        return [user for user in self._cached_users if not user.email]


def home_page(request: HttpRequest) -> HttpResponse:
    """Render the home page for the application.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: The HTTP response.
    """
    context = {
        "userinfo": UserInfo(),
        "warnings": USER_COUNT_PROBLEM_MESSAGES,
    }
    return render(request, "pages/home.html", context)


def agent_list(request: HttpRequest) -> HttpResponse:
    """Render the list of Agent users.

    Or more precisely, we want to - for the benefit of Marnie - map between each
    Agent, and the jobs created by them, in something spiritually similar to a
    'per-agent spreadsheet'

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: The HTTP response.
    """
    # Only Marnie user may access this view. Return a 403 Forbidden response if some
    # other user is trying to access this view.
    user = cast(User, request.user)
    if not user.is_marnie:
        return HttpResponse(status=403)
    context = {"agent_list": User.objects.filter(is_agent=True)}
    return render(request, "jobs/agent_list.html", context=context)


class JobDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):  # type: ignore[type-arg]
    """Display details of a specific Maintenance Job."""

    model = Job

    def test_func(self) -> bool:
        """Check the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        user = cast(User, self.request.user)
        obj = self.get_object()
        return user.is_marnie or user == obj.agent

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add additional context data to the template.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The context data.
        """
        # Only Marnie can see the Edit link.
        user = cast(User, self.request.user)
        edit_link_present = user.is_marnie
        context = super().get_context_data(**kwargs)
        context["edit_link_presnt"] = edit_link_present
        return context


class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):  # type: ignore[type-arg]
    """Update a Maintenance Job."""

    queryset = Job.objects.all()
    fields = ["date"]
    template_name = "jobs/job_update.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        # Only Marnie and Admin users can reach this view.
        user = cast(User, self.request.user)
        return user.is_marnie or user.is_superuser
