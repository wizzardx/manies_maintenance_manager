"""Provide a view to create a new Maintenance Job."""

import logging
from typing import Any

import environ
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from typeguard import check_type

from manies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from manies_maintenance_manager.jobs.exceptions import ManieUserNotFoundError
from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.utils import generate_email_body
from manies_maintenance_manager.jobs.utils import get_manie_email
from manies_maintenance_manager.jobs.utils import get_sysadmin_email
from manies_maintenance_manager.jobs.utils import user_has_verified_email_address
from manies_maintenance_manager.users.models import User

env = environ.Env()
SKIP_EMAIL_SEND = env.bool("SKIP_EMAIL_SEND", default=False)

logger = logging.getLogger(__name__)


def _manie_has_verified_email_address(manie_email: str) -> bool:
    """Check if Manie has a verified email address.

    Args:
        manie_email (str): The email address for Manie.

    Returns:
        bool: True if Manie has a verified email address, False otherwise.
    """
    return check_type(
        User.objects.get(email=manie_email)
        .emailaddress_set.filter(  # type: ignore[attr-defined]
            verified=True,
        )
        .exists(),
        bool,
    )


def _log_exception_and_flash_for_manie_user_not_found(request: HttpRequest) -> None:
    """Log an exception and send a flash message for a Manie user not found.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.exception(
        "No Manie user found. Unable to send maintenance request email.",
    )
    messages.error(
        request,
        "No Manie user found.\nUnable to send maintenance request email.\n"
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


def _log_error_and_flash_for_manie_user_no_email_address(request: HttpRequest) -> None:
    """Log an error and send a flash message for a Manie user with no email address.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.error(
        "User manie has no email address. Unable to send maintenance request email.",
    )
    messages.error(
        request,
        "Manie's email address is missing.\nUnable to send maintenance "
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


def _log_error_and_flash_for_manie_user_no_verified_email_address(
    request: HttpRequest,
) -> None:
    """Log error and send a flash message for a Manie user with no verified email.

    Args:
        request (HttpRequest): The HTTP request.
    """
    logger.error(
        "Manie's email address is not verified. "
        "Unable to send maintenance request email.",
    )
    messages.error(
        request,
        "Manie's email address is not verified.\nUnable to send maintenance "
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

    def form_valid(  # pylint: disable=too-complex
        self,
        form: Any,
    ) -> HttpResponse:
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

        # Check that the user is logged in and that they are an Agent. All of
        # that should already be setup before the logic gets here, but just in case:

        if not self.request.user.is_authenticated:  # pragma: no cover
            msg = "User is not authenticated"
            raise ValueError(msg)

        if not self.request.user.is_agent:  # pragma: no cover
            msg = "User is not an agent"
            raise ValueError(msg)

        # Make sure that the "agent" field is set to the current user, before we
        # save to the database.
        form.instance.agent = self.request.user

        # Call validations/etc on parent classes
        response = super().form_valid(form)

        # Send an email notification
        # Over here, `job` is the JOb object that has just been created and saved.
        if not (job := self.object):  # pragma: no cover
            msg = "Job object is missing"
            raise ValueError(msg)

        email_subject = f"New maintenance request by {job.agent.username}"
        email_body = generate_email_body(job, self.request)

        email_from = DEFAULT_FROM_EMAIL
        email_cc = self.request.user.email

        # One main error that can happen here is if the Manie user account does
        # not exist.
        try:
            manie_email = get_manie_email()
        except ManieUserNotFoundError:
            # Log the message here, then send a flash message to the user (it
            # will appear on their next web page). We don't raise an exception
            # further than this point.
            _log_exception_and_flash_for_manie_user_not_found(
                self.request,
            )
            return response

        # Manie's user account was found. Next, check the user's own email address
        # to see if it's valid. If it's not, we can't send the email.
        if not self.request.user.email:
            # The user's email address is missing. Log the message, then send a
            # flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_user_no_email_address(self.request)
            return response

        # User's email address was found. Check if Manie user has an email address.
        if not manie_email:
            # The Manie user's email address is missing. Log the message, then send
            # a flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_manie_user_no_email_address(self.request)
            return response

        # Check if the agent user has a verified email address
        if not user_has_verified_email_address(self.request.user):
            # The user's email address is not verified. Log the message, then send a
            # flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_user_no_verified_email_address(self.request)
            return response

        # Check if Manie has a verified email address
        if not _manie_has_verified_email_address(manie_email=manie_email):
            # Manie's email address is not verified. Log the message, then send a
            # flash message to the user (it will appear on their next web page).
            _log_error_and_flash_for_manie_user_no_verified_email_address(self.request)
            return response

        # Manie's user account and other required details were found, so we can
        # send the email:
        email_to = get_manie_email()

        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=email_from,
            to=[email_to],
            cc=[email_cc],
        )

        if not SKIP_EMAIL_SEND:
            email.send()
        else:
            logger.info(
                "Skipping email send. Would have sent the following email:\n\n"
                "Subject: %s\n\n"
                "Body: %s\n\n"
                "From: %s\n\n"
                "To: %s\n\n"
                "CC: %s\n\n",
                email_subject,
                email_body,
                email_from,
                email_to,
                email_cc,
            )

        # And send the success flash message to the user:
        messages.success(
            self.request,
            "Your maintenance request has been sent to Manie.",
        )

        return response

    def test_func(self) -> bool:
        """Check if the user is an agent, or Manie, or a superuser.

        Returns:
            bool: True if the user has the required permissions, False otherwise.
        """
        user = check_type(self.request.user, User)
        return user.is_agent or user.is_superuser
