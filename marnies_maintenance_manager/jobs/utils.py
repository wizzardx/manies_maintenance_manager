"""Utility functions for the jobs app."""

import logging
from typing import TypeVar

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models import QuerySet

from .exceptions import LogicalError
from .exceptions import MarnieUserNotFoundError
from .exceptions import MultipleMarnieUsersError
from .exceptions import NoSystemAdministratorUserError

User = get_user_model()


logger = logging.getLogger(__name__)


def get_marnie_email() -> str:
    """
    Return the email address for Marnie.

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


def get_sysadmin_email(*, _introduce_logic_error: bool = False) -> str:
    """
    Return the email address for the system administrator.

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
    msg = "Reached logically impossible branch in get_sysadmin_email."
    logger.critical(msg)
    raise LogicalError(msg)


# Define a type variable that can be any subclass of Django's Model
T = TypeVar("T", bound=Model)


def first_or_error(queryset: QuerySet[T], error_message: str = "No object found.") -> T:
    """
    Return the first object of a queryset, or raise an error if the queryset is empty.

    Args:
        queryset (QuerySet[T]): The queryset from which to retrieve the first object.
        error_message (str): Custom error message to raise if no objects are found.

    Returns:
        T: The first object in the queryset.

    Raises:
        ObjectDoesNotExist: If the queryset is empty.
    """
    obj = queryset.first()
    if obj is None:
        raise ObjectDoesNotExist(error_message)
    return obj


def count_admin_users() -> int:
    """
    Return the number of superusers.

    Returns:
        int: The number of superusers.
    """
    return User.objects.filter(is_superuser=True).count()


def count_marnie_users() -> int:
    """
    Return the number of Marnie users.

    Returns:
        int: The number of Marnie users.
    """
    return User.objects.filter(is_marnie=True).count()


def count_agent_users() -> int:
    """
    Return the number of Agent users.

    Returns:
        int: The number of Agent users.
    """
    return User.objects.filter(is_agent=True).count()
