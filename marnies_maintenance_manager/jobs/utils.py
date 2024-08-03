"""Utility functions for the "jobs" app."""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Protocol
from typing import TypeVar
from uuid import UUID

import environ
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.db.models import Model
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.constants import POST_METHOD_NAME
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

from .exceptions import EnvironmentVariableNotSetError
from .exceptions import LogicalError
from .exceptions import MarnieUserNotFoundError
from .exceptions import MultipleMarnieUsersError
from .exceptions import NoSystemAdministratorUserError

env = environ.Env()
SKIP_EMAIL_SEND = env.bool("SKIP_EMAIL_SEND", default=False)

logger = logging.getLogger(__name__)


def get_marnie_email() -> str:
    """Return the email address for Marnie.

    Returns:
        str: The email address for Marnie.

    Raises:
        MarnieUserNotFoundError: If no Marnie user is found.
        MultipleMarnieUsersError: If multiple Marnie users are found.
    """
    try:
        marnie = User.objects.get(is_marnie=True)
    except User.DoesNotExist as err:
        raise MarnieUserNotFoundError from err
    except User.MultipleObjectsReturned as err:
        raise MultipleMarnieUsersError from err
    return marnie.email


# pylint: disable=useless-param-doc, useless-type-doc
def get_sysadmin_email(*, _introduce_logic_error: bool = False) -> str:
    """Return the email address for the system administrator.

    Args:
        _introduce_logic_error (bool): If True, introduces a logical error for testing
                                       purposes.

    Returns:
        str: The email address for the system administrator.

    Raises:
        LogicalError: If a logical error is encountered.
        NoSystemAdministratorUserError: If no system administrator user is found.
    """
    sysadmins = User.objects.filter(is_superuser=True)

    # pylint: disable=consider-ternary-expression
    if _introduce_logic_error:  # noqa: SIM108
        num_sysadmins_found = -1  # Simulate a logical error for testing.
    else:
        num_sysadmins_found = sysadmins.count()

    if num_sysadmins_found == 0:
        raise NoSystemAdministratorUserError

    if num_sysadmins_found > 1:
        # Found more than one sysadmin. Log a warning, and then return the email
        # address of the first one found.
        sysadmin = first_or_error(sysadmins)
        logger.warning(
            "Multiple system administrator users found. Defaulting to the first "
            "user found, with system id: %s",
            sysadmin.id,
        )
        return sysadmin.email

    # The coverage tool doesn't detect this branch properly, so we need to tell it to
    # ignore it. The line coverage still works, though.
    if num_sysadmins_found == 1:  # pragma: no branch
        # Found exactly one sysadmin, return the email
        return first_or_error(sysadmins).email

    # This case should be logically impossible
    msg = "Reached logically impossible branch in get_sysadmin_email"
    logger.critical(msg)
    raise LogicalError(msg)


# Define a type variable that can be any subclass of Django's Model
T = TypeVar("T", bound=Model)


def first_or_error(queryset: QuerySet[T], error_message: str = "No object found") -> T:
    """Return first object of a queryset, or raise an error if the queryset is empty.

    Args:
        queryset (QuerySet[T]): The queryset from which to retrieve the first object.
        error_message (str): Custom error message to raise if no objects are found.

    Returns:
        T: The first object in the queryset.

    Raises:
        ObjectDoesNotExist: If the queryset is empty.
    """
    if (obj := queryset.first()) is None:
        raise ObjectDoesNotExist(error_message)
    return obj


def count_admin_users() -> int:
    """Return the number of superusers.

    Returns:
        int: The number of superusers.
    """
    return User.objects.filter(is_superuser=True).count()


def count_marnie_users() -> int:
    """Return the number of Marnie users.

    Returns:
        int: The number of Marnie users.
    """
    return User.objects.filter(is_marnie=True).count()


def count_agent_users() -> int:
    """Return the number of Agent users.

    Returns:
        int: The number of Agent users.
    """
    return User.objects.filter(is_agent=True).count()


def user_has_verified_email_address(user: User) -> bool:
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


def get_test_user_password(key: str = "TEST_USER_PASSWORD") -> str:
    """Return the password for test users.

    Args:
        key (str): The environment variable key to retrieve the password from.

    Returns:
        str: The password for test users.

    Raises:
        EnvironmentVariableNotSetError: If the environment variable is not set.
    """
    # Retrieve the password from the TEST_USER_PASSWORD environment variable
    try:
        return os.environ[key]
    except KeyError as err:
        msg = f"{key} environment variable not set"
        raise EnvironmentVariableNotSetError(msg) from err


def quote_accept_or_reject(
    request: HttpRequest,
    pk: UUID,
    *,
    accepted: bool,
    skip_email_send: bool = SKIP_EMAIL_SEND,
) -> HttpResponse:
    """Accept or reject the quote for a specific Maintenance Job.

     Args:
         request (HttpRequest): The HTTP request.
         pk (UUID): The primary key of the Job instance.
         accepted (bool): True if the quote is accepted, False if it is rejected.
         skip_email_send (bool): If True, skip sending the email.

    Returns:
         HttpResponse: The HTTP response.
    """
    verb = "accept" if accepted else "reject"

    # Only the POST method is allowed.
    if request.method != POST_METHOD_NAME:
        return HttpResponse(
            "Method not allowed",
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # Fail for nonexistent jobs
    job = get_object_or_404(Job, pk=pk)

    # Return a permission error if the user is not an agent.
    user = check_type(request.user, User)

    # Only the agent who created the quote may accept or reject it.
    # Besides them, admin users can always accept or reject quotes.
    if not (user.is_superuser or (user.is_agent and user == job.agent)):
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)

    # Return an error if the job is not in the correct state.
    if job.status not in {
        Job.Status.QUOTE_UPLOADED.value,
        Job.Status.QUOTE_REJECTED_BY_AGENT.value,
    }:
        return HttpResponse(
            f"Job is not in the correct state for {verb}ing a quote.",
            status=status.HTTP_412_PRECONDITION_FAILED,
        )

    # Change the job state to 'quote accepted' or 'quote rejected'
    if accepted:
        job.status = Job.Status.QUOTE_ACCEPTED_BY_AGENT.value
        job.accepted_or_rejected = Job.AcceptedOrRejected.ACCEPTED.value
    else:
        job.status = Job.Status.QUOTE_REJECTED_BY_AGENT.value
        job.accepted_or_rejected = Job.AcceptedOrRejected.REJECTED.value

    # Save the changes to the job
    job.save()

    # Get full URL for the job detail view
    job_detail_url = request.build_absolute_uri(job.get_absolute_url())

    # Send email to Marnie telling him that his quote was accepted by the agent
    email_subject = f"Quote {verb}ed by {job.agent.username}"
    email_body = (
        f"Agent {job.agent.username} has {verb}ed the quote for a maintenance job.\n\n"
        f"Details of the job can be found at: {job_detail_url}\n\n"
        "Details of the original request:\n\n"
        "-----\n\n"
        "Subject: Quote for your maintenance request\n\n"
        "-----\n\n"
        f"Subject: New maintenance request by {job.agent.username}\n\n"
        f"Marnie performed the inspection on {job.date_of_inspection} and has "
        "quoted you.\n\n"
    )

    # Call the email body-generation logic used previously, to help us populate
    # the rest of this email body:
    email_body += generate_email_body(job, request)

    email_from = DEFAULT_FROM_EMAIL
    email_to = get_marnie_email()
    email_cc = job.agent.email

    # Create the email message:
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=email_from,
        to=[email_to],
        cc=[email_cc],
    )

    # Send the mail:
    if not skip_email_send:
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

    # Send a success flash message to the user:
    messages.success(request, f"Quote {verb}ed. An email has been sent to Marnie.")

    # Redirect to the detail view for this job.
    return HttpResponseRedirect(job.get_absolute_url())


def generate_email_body(job: Job, request: HttpRequest) -> str:
    """Generate the email body for the maintenance request email.

    Args:
        job (Job): The Job object.
        request (HttpRequest): The HTTP request.

    Returns:
        str: The email body.
    """
    # Get full URL for the job detail view
    job_detail_url = request.build_absolute_uri(job.get_absolute_url())

    return (
        f"{job.agent.username} has made a new maintenance request.\n\n"
        f"Details of the job can be found at: {job_detail_url}\n\n"
        f"Number: {job.number}\n\n"
        f"Date: {job.date}\n\n"
        f"Address Details:\n\n{job.address_details}\n\n"
        f"GPS Link:\n\n{job.gps_link}\n\n"
        f"Quote Request Details:\n\n{job.quote_request_details}\n\n"
        f"PS: This mail is sent from an unmonitored email address. "
        "Please do not reply to this email.\n\n"
    )


class TellAndSeekable(Protocol):
    """A protocol for files that can be told and seeked."""

    def tell(self) -> int:
        """Return the current file position."""

    def seek(self, offset: int) -> None:
        """Seek to the specified offset in the file.

        Args:
            offset (int): The offset to seek to.
        """


@contextmanager
def safe_read(*args: TellAndSeekable) -> Generator[None, None, None]:
    """Ensure that the file is read from the beginning and reset the file pointer after.

    Args:
        *args (TellAndSeekable): The files to read.

    Raises:
        AssertionError: If the file pointer is not reset to 0 before reading or not
            advanced after reading.d

    Yields:
        None: The context manager yields nothing.


    """
    for f in args:
        location = f.tell()
        # Skip mocked return values:
        if repr(location).startswith("<Mock "):
            continue
        if location != 0:
            msg = "File pointer not reset to 0 before reading."
            raise AssertionError(msg)

    try:
        yield
    finally:
        for f in args:
            location = f.tell()
            # Skip mocked return values:
            if repr(location).startswith("<Mock "):
                continue
            if location == 0:
                msg = "File pointer not reset to 0 after reading."
                raise AssertionError(msg)
            f.seek(0)
