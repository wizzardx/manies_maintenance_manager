"""Utility functions for the "jobs" app."""

import logging
import os
from typing import TypeVar

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models import QuerySet

from marnies_maintenance_manager.users.models import User

from .exceptions import EnvironmentVariableNotSetError
from .exceptions import LogicalError
from .exceptions import MarnieUserNotFoundError
from .exceptions import MultipleMarnieUsersError
from .exceptions import NoSystemAdministratorUserError

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


def first_or_error(queryset: QuerySet[T], error_message: str = "No object found.") -> T:
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


def make_test_user(  # noqa: PLR0913  # pylint: disable=too-many-arguments
    django_user_model: type[User],
    username: str,
    *,
    is_agent: bool = False,
    is_superuser: bool = False,
    is_marnie: bool = False,
    email_verified: bool = True,
    email_primary: bool = True,
) -> User:
    """Create and return a new user with optional agent and superuser status.

    This function helps in creating a user instance with additional properties
    like being an agent or a superuser. It sets the username and password,
    marks the email as verified, and assigns the role based on the parameters.

    Args:
        django_user_model (type[User]): The User model used to create new users.
        username (str): The username for the new user.
        is_agent (bool): Flag to indicate if the user is an agent.
        is_superuser (bool): Flag to indicate if the user is a superuser.
        is_marnie (bool): Flag to indicate if the user is Marnie.
        email_verified (bool): Flag to indicate if the email is verified.
        email_primary (bool): Flag to indicate if the email is the primary email.

    Returns:
        User: The newly created user instance.
    """
    user_ = django_user_model.objects.create_user(
        username=username,
        password=get_test_user_password(),
        is_agent=is_agent,
        is_superuser=is_superuser,
        is_marnie=is_marnie,
        email=f"{username}@example.com",
    )
    user_.emailaddress_set.create(  # type: ignore[attr-defined]
        email=f"{username}@example.com",
        primary=email_primary,
        verified=email_verified,
    )
    return user_
