"""Test utility functions used by both the functional tests and the other tests.

By other tests, I mean the unit tests and the integration tests.

"""

from collections.abc import Generator
from contextlib import contextmanager

import environ

from manies_maintenance_manager.jobs.utils import get_test_user_password
from manies_maintenance_manager.users.models import User

env = environ.Env()

DEPRECATION_WARNINGS_EXPECTED = env.bool(
    "DEPRECATION_WARNINGS_EXPECTED",
    default=True,
)


TEST_USERS_SHOULD_ALREADY_EXIST = env.bool(
    "TEST_USERS_SHOULD_ALREADY_EXIST",
    default=False,
)


@contextmanager
def suppress_fastdev_strict_if_deprecation_warning(
    deprecation_warnings_expected: bool = DEPRECATION_WARNINGS_EXPECTED,  # noqa: FBT001
) -> Generator[None, None, None]:
    """Context manager to suppress a specific FASTDEV_STRICT_IF deprecation warning.

    Args:
        deprecation_warnings_expected (bool): Flag to indicate if the deprecation
            warning is expected. Defaults to True.

    Django-FastDev causes a DeprecationWarning to be logged when using the
    # {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    # while handling a GET request to the /accounts/login/ URL. We can ignore this
    # for our testing.

    Example:
         >>> with suppress_fastdev_strict_if_deprecation_warning():
         ...     import warnings
         ...     warnings.warn("set FASTDEV_STRICT_IF in settings, and use "
         ...                   "{% ifexists %} instead of {% if %}", DeprecationWarning)

     Yields:
         None: The context manager does not return anything.
    """
    if deprecation_warnings_expected:
        import pytest  # pylint: disable=import-outside-toplevel

        with pytest.warns(
            DeprecationWarning,
            match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} "
            "instead of {% if %}",
        ):
            yield
    else:
        yield


def make_test_user(  # noqa: PLR0913  # pylint: disable=too-many-arguments
    django_user_model: type[User],
    username: str,
    *,
    is_agent: bool = False,
    is_superuser: bool = False,
    is_staff: bool = False,
    is_manie: bool = False,
    email_verified: bool = True,
    email_primary: bool = True,
    user_should_already_exist: bool = TEST_USERS_SHOULD_ALREADY_EXIST,
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
        is_staff (bool): Flag to indicate if the user is a staff member, and can
            access the Django admin interface.
        is_manie (bool): Flag to indicate if the user is Manie.
        email_verified (bool): Flag to indicate if the email is verified.
        email_primary (bool): Flag to indicate if the email is the primary email.
        user_should_already_exist (bool): Flag to indicate if the user should already
            exist in the database.

    Returns:
        User: The newly created user instance.
    """
    if user_should_already_exist:
        # Confirm that the user exists, and return it:
        return django_user_model.objects.get(username=username)

    user_ = django_user_model.objects.create_user(
        username=username,
        password=get_test_user_password(),
        is_agent=is_agent,
        is_superuser=is_superuser,
        is_staff=is_staff,
        is_manie=is_manie,
        email=f"{username}@example.com",
    )
    user_.emailaddress_set.create(  # type: ignore[attr-defined]
        email=f"{username}@example.com",
        primary=email_primary,
        verified=email_verified,
    )
    return user_
