"""Unit tests for the home page view."""

# pylint: disable=unused-argument,no-self-use,magic-value-comparison

import functools

import pytest
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.tests.views.utils import HTTP_SUCCESS_STATUS_CODE
from marnies_maintenance_manager.jobs.tests.views.utils import (
    check_basic_page_html_structure,
)
from marnies_maintenance_manager.jobs.utils import count_admin_users
from marnies_maintenance_manager.jobs.utils import count_agent_users
from marnies_maintenance_manager.jobs.utils import count_marnie_users
from marnies_maintenance_manager.jobs.utils import get_test_user_password
from marnies_maintenance_manager.jobs.views.home_page_view import (
    USER_COUNT_PROBLEM_MESSAGES,
)
from marnies_maintenance_manager.users.models import User

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


class TestBasicHomePageText:
    """Test the basic welcome text on the home page."""

    @pytest.mark.django_db()
    def test_basic_welcome_text(self, client: Client) -> None:
        """Test the basic welcome text on the home page.

        Args:
            client (Client): A test client for an unknown user.
        """
        response = client.get(reverse("home"))
        assert response.status_code == status.HTTP_200_OK
        assert "Welcome to Marnie's Maintenance Manager!" in str(
            response.content.decode(),
        )

    @pytest.mark.django_db()
    def test_generic_django_cookicutter_text_not_displayed(
        self,
        client: Client,
    ) -> None:
        """Test that the generic Django Cookiecutter text is not displayed.

        Args:
            client (Client): A test client for an unknown user.
        """
        response = client.get(reverse("home"))
        assert response.status_code == status.HTTP_200_OK
        assert (
            "Use this document as a way to quick start any new project."
            not in response.content.decode()
        )

    @pytest.mark.django_db()
    def test_not_signed_in(self, client: Client) -> None:
        """Test the home page for an unknown user.

        Args:
            client (Client): A test client for an unknown user.
        """
        response = client.get(reverse("home"))
        assert response.status_code == status.HTTP_200_OK
        assert (
            "Please Sign In to the system to book a home visit by Marnie."
            in response.content.decode()
        )
        assert (
            "If you don't have an account yet, then please Sign Up!"
            in response.content.decode()
        )

    @pytest.mark.django_db()
    def test_marnie_signed_in(self, marnie_user_client: Client) -> None:
        """Test the home page for Marnie.

        Args:
            marnie_user_client (Client): A test client for user Marnie.
        """
        response = marnie_user_client.get(reverse("home"))
        assert response.status_code == status.HTTP_200_OK
        assert (
            'Welcome back, Marnie. You can click on the "Agents" link above, to see '
            'the per-Agent listing of Maintenance Jobs, aka their "spreadsheets."'
            in response.content.decode()
        )

    @pytest.mark.django_db()
    def test_agent_signed_in(self, bob_agent_user_client: Client) -> None:
        """Test the home page for an agent user.

        Args:
            bob_agent_user_client (Client): A test client for agent user Bob.
        """
        response = bob_agent_user_client.get(reverse("home"))
        assert response.status_code == status.HTTP_200_OK
        assert (
            'Welcome back. You can click the "Maintenance Jobs" link above, to see '
            "the list of Maintenance Visits scheduled for Marnie."
            in response.content.decode()
        )

    @pytest.mark.django_db()
    def test_unknown_user_signed_in(self, unknown_user_client: Client) -> None:
        """Test the home page for an unknown user.

        Args:
            unknown_user_client (Client): A test client for an unknown user.
        """
        response = unknown_user_client.get(reverse("home"))
        assert response.status_code == status.HTTP_200_OK
        assert (
            "You're signed in to this website, but we don't know who you are!"
            in response.content.decode()
        )
        assert (
            "If you're a property agent, then please contact Marnie so that this "
            "website can be setup for you!" in response.content.decode()
        )


def test_limited_number_of_queries_on_home_page_for_admin_user(
    superuser_client: Client,
    django_assert_max_num_queries: functools.partial,  # type: ignore[type-arg]
) -> None:
    """Test the number of queries on the home page for a superuser.

    To help us avoid various N+1 issues with querying on the home page for Admin user.

    Args:
        superuser_client (Client): A test client for a superuser.
        django_assert_max_num_queries (functools.partial): Pytest fixture to check the
            number of queries executed.
    """
    with django_assert_max_num_queries(6):
        superuser_client.get(reverse("home"))


@pytest.mark.django_db()
def test_home_page_returns_correct_html(client: Client) -> None:
    """Verify that the home page renders correctly.

    Args:
        client (Client): Django test client used to make requests.
    """
    check_basic_page_html_structure(
        client=client,
        url="/",
        expected_title="Marnie's Maintenance Manager",
        expected_h1_text=None,
        expected_template_name="pages/home.html",
        expected_func_name="home_page",
        expected_url_name="home",
        expected_view_class=None,
    )


class TestAdminSpecificHomePageWarnings:
    """Tests for the home page warnings related to Admin users."""

    # pylint: disable=too-many-public-methods

    # Tests for when there are no admin users

    def test_warning_for_no_admin_user(self, bob_agent_user_client: Client) -> None:
        """Test that a warning is shown when there are no Admin users.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
        """
        # Make sure there are no admin users here
        assert count_admin_users() == 0

        response = bob_agent_user_client.get("/")

        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_ADMIN_USERS"] in response.content.decode()
        )

    def test_no_warning_for_no_admin_user_when_there_is_an_admin_usr(
        self,
        admin_client: Client,
    ) -> None:
        """Ensure no warning for no Admin users when there is an Admin user.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Make sure there is at least one admin user
        assert count_admin_users() >= 1

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_ADMIN_USERS"]
            not in response.content.decode()
        )

    # Tests for when there are multiple admin users in the system.

    def test_warning_for_multiple_admin_users(
        self,
        bob_agent_user: User,
        peter_agent_user: User,
        admin_client: Client,
    ) -> None:
        """Test that a warning is shown when there are multiple Admin users.

        Args:
            admin_client (Client): A test client with admin privileges.
            bob_agent_user (User): User instance for Bob, temporarily made an admin
                                   for this test.
            peter_agent_user (User): User instance for Peter, also an admin.
        """
        # Change Bob to an admin so that there are two admin users.
        bob_agent_user.is_superuser = True
        bob_agent_user.save()

        # Make sure there are at least 2 admin users here:
        assert count_admin_users() >= 2  # noqa: PLR2004

        # We can check now.
        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["MANY_ADMIN_USERS"] in response.content.decode()
        )

    def test_no_warnings_for_multiple_admins_when_there_is_one_admin(
        self,
        admin_client: Client,
    ) -> None:
        """Ensure no warning for multiple Admin users when there is only one Admin user.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Make sure there is only one admin user
        assert count_admin_users() == 1

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["MANY_ADMIN_USERS"]
            not in response.content.decode()
        )

    # noinspection PyUnusedLocal
    def test_no_warning_for_multiple_admin_users_when_i_am_not_admin(
        self,
        admin_user: User,
        peter_agent_user: User,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure no admin user multiple warning when not admin.

        Args:
            admin_user (User): An admin user instance.
            peter_agent_user (User): Another user with admin status.
            bob_agent_user_client (Client): Bob's client, who is not an admin.
        """
        # Make sure there are two admin users:
        peter_agent_user.is_superuser = True
        peter_agent_user.save()

        # Make sure there are at least 2 admin users here:
        assert count_admin_users() >= 2  # noqa: PLR2004

        response = bob_agent_user_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["MANY_ADMIN_USERS"]
            not in response.content.decode()
        )

    # Tests for when there is no Marnie user in the system

    def test_warning_for_no_marnie_user(self, admin_client: Client) -> None:
        """Test that a warning is shown when there are no Marnie users.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Make sure there are no Marnie users here
        assert count_marnie_users() == 0

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_MARNIE_USERS"] in response.content.decode()
        )

    def test_no_warning_for_no_marnie_user_when_there_is_a_marnie_user(
        self,
        marnie_user: User,
        admin_client: Client,
    ) -> None:
        """Ensure no warning for no Marnie users when there is a Marnie user.

        Args:
            marnie_user (User): User instance representing Marnie.
            admin_client (Client): A test client with admin privileges.
        """
        # Make sure there is at least one Marnie user
        assert count_marnie_users() >= 1

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_MARNIE_USERS"]
            not in response.content.decode()
        )

    def test_no_warning_for_no_marnie_user_when_i_am_not_admin(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """Test there is no warning for no Marnie users when the user is not an admin.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, who is an
                                            agent but not an admin.
        """
        # Make sure there are no Marnie users here
        assert count_marnie_users() == 0

        # Make sure there are no admins here, either.
        assert count_admin_users() == 0

        response = bob_agent_user_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_MARNIE_USERS"]
            not in response.content.decode()
        )

    # Tests for when there are multiple Marnie users.

    def test_warning_for_multiple_marnie_users(
        self,
        marnie_user: User,
        bob_agent_user: User,
        admin_client: Client,
    ) -> None:
        """Test that a warning is shown when there are multiple Marnie users.

        Args:
            admin_client (Client): A test client with admin privileges.
            bob_agent_user (User): User instance for Bob, temporarily made a Marnie
                                   user for this test.
            marnie_user (User): User instance representing Marnie.
        """
        # Make sure there are at least 2 Marnie users here
        bob_agent_user.is_marnie = True
        bob_agent_user.save()
        assert count_marnie_users() >= 2  # noqa: PLR2004

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["MANY_MARNIE_USERS"]
            in response.content.decode()
        )

    def test_no_warning_for_multiple_marnie_users_when_there_is_one_marnie_user(
        self,
        marnie_user: User,
        admin_client: Client,
    ) -> None:
        """Ensure no warning for multiple Marnie users when there is one Marnie user.

        Args:
            marnie_user (User): User instance representing Marnie.
            admin_client (Client): A test client with admin privileges.
        """
        # Make sure there is only one Marnie user
        assert count_marnie_users() == 1

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["MANY_MARNIE_USERS"]
            not in response.content.decode()
        )

    def test_no_warning_for_multiple_marnie_users_when_i_am_not_admin(
        self,
        marnie_user: User,
        bob_agent_user: User,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure no Marnie user multiple warning when not an admin.

        Args:
            bob_agent_user (User): User instance for Bob, marked as a Marnie user.
            bob_agent_user_client (Client): A test client for Bob, who is an agent but
                                            not an admin.
            marnie_user (User): Another user instance flagged as Marnie to simulate the
                                test condition.
        """
        # Make sure there are at least 2 Marnie users here
        # We have a single 'marnie' user already, lets flag 'bob' as a 'marnie' user,
        # too.
        bob_agent_user.is_marnie = True
        bob_agent_user.save()

        assert count_marnie_users() >= 2  # noqa: PLR2004

        # Make sure there are no admins here.
        assert count_admin_users() == 0

        response = bob_agent_user_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["MANY_MARNIE_USERS"]
            not in response.content.decode()
        )

    # Tests for when there are no agent users

    def test_warning_for_no_agent_users(self, admin_client: Client) -> None:
        """Test that a warning is shown when there are no Agent users.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Make sure there are no agent users here
        assert count_agent_users() == 0

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_AGENT_USERS"] in response.content.decode()
        )

    def test_no_warning_for_no_agent_users_when_there_is_an_agent_user(
        self,
        bob_agent_user: User,
        admin_client: Client,
    ) -> None:
        """Ensure no warning for no Agent users when there is an Agent user.

        Args:
            bob_agent_user (User): User instance for Bob, an agent user.
            admin_client (Client): A test client with admin privileges.
        """
        # Make sure there is at least one agent user
        assert count_agent_users() >= 1

        response = admin_client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_AGENT_USERS"]
            not in response.content.decode()
        )

    @pytest.mark.django_db()
    def test_no_warning_for_no_agent_users_when_i_am_not_admin(
        self,
        client: Client,
    ) -> None:
        """Test that there is no warning for no Agent users when I am not an admin.

        Args:
            client (Client): A general test client, not configured as an admin.
        """
        # Make sure there are no agent users in the system
        assert count_agent_users() == 0

        # Make sure there are no admin users in the system
        assert count_admin_users() == 0

        # Check, as anonymous user on the browser that there are no warnings for no
        # agents.
        response = client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE
        assert (
            USER_COUNT_PROBLEM_MESSAGES["NO_AGENT_USERS"]
            not in response.content.decode()
        )

    # Tests for when there are users with no email addresses

    def test_warning_for_users_with_no_email_addresses(
        self,
        admin_client: Client,
    ) -> None:
        """Test that a warning is shown when there are users with no email addresses.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with no email address
        username = "no_email_user"
        User.objects.create(username=username)

        response = admin_client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES["NO_EMAIL_ADDRESS"]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg in response.content.decode()

    @pytest.mark.django_db()
    def test_no_missing_email_warning_for_users_with_email(
        self,
        admin_client: Client,
    ) -> None:
        """Test no warning for users with email addresses.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with an email address
        username = "terry"
        User.objects.create(username=username, email="terry@email.com")

        response = admin_client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES["NO_EMAIL_ADDRESS"]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg not in response.content.decode()

    @pytest.mark.django_db()
    def test_no_warning_for_users_with_no_email_addresses_when_i_am_not_admin(
        self,
        client: Client,
    ) -> None:
        """Test for no warning for users with no email addresses when I am not an admin.

        Args:
            client (Client): A general test client, not configured as an admin.
        """
        # Create a user with no email address
        username = "no_email_user"
        User.objects.create(username=username)

        response = client.get("/")
        assert response.status_code == HTTP_SUCCESS_STATUS_CODE

        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES["NO_EMAIL_ADDRESS"]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg not in response.content.decode()

    # Tests for when there are users with unverified email addresses

    def test_warning_for_users_with_no_verified_email_addresses(
        self,
        admin_client: Client,
    ) -> None:
        """Test warning for users with unverified email addresses.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with an unverified email address
        username = "unverified_email_user"
        User.objects.create(
            username=username,
            email="unverified_email_user@example.com",
        )

        response = admin_client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES[
            "NO_VERIFIED_EMAIL_ADDRESS"
        ]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg in response.content.decode()

    def test_no_warning_unverified_email_for_users_with_verified_email(
        self,
        admin_client: Client,
    ) -> None:
        """Test no warning for users with verified email addresses.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with a verified email address
        username = "jack"
        user = User.objects.create(
            username=username,
            email=f"{username}@email.com",
        )
        user.emailaddress_set.create(  # type: ignore[attr-defined]
            email=f"{username}@email.com",
            primary=True,
            verified=True,
        )

        response = admin_client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES[
            "NO_VERIFIED_EMAIL_ADDRESS"
        ]
        expected_msg = expected_msg_template.format(username=username)

        assert expected_msg not in response.content.decode()

    @pytest.mark.django_db()
    def test_no_warning_verified_email_non_admin(self, client: Client) -> None:
        """Test warning for users with verified email addresses.

        Args:
            client (Client): A test client.
        """
        # Create a user with an unverified email address
        username = "verified_email_user"
        User.objects.create(
            username=username,
            email="verified_email_user@example.com",
        )

        response = client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES[
            "NO_VERIFIED_EMAIL_ADDRESS"
        ]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg not in response.content.decode()

    def test_no_warning_verified_email_admin(
        self,
        superuser_user: User,
        superuser_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Test no warning for verified email addresses when the user is an admin.

        Args:
            superuser_user (User): A superuser instance with verified email address.
            superuser_client (Client): A test client configured for a superuser.
            bob_agent_user (User): User instance for Bob, who is an agent with a
                verified email address.
        """
        response = superuser_client.get("/")

        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES[
            "NO_VERIFIED_EMAIL_ADDRESS"
        ]
        expected_msg = expected_msg_template.format(username=superuser_user.username)
        assert expected_msg not in response.content.decode()

    # Tests for when there are users who do not have a primary email address

    def test_warning_for_users_with_no_primary_email_address(
        self,
        admin_client: Client,
    ) -> None:
        """Test that a warning is shown.

        - When there are users with no primary email address.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with no primary email address
        (expected_msg, response) = _create_user_and_check_no_primary_email_warning(
            admin_client,
        )
        assert expected_msg in response.content.decode()

    def test_no_warning_for_users_with_primary_email_address(
        self,
        admin_client: Client,
    ) -> None:
        """Ensure no warning for users with a primary email address.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with a primary email address
        username = "primary_email_user"
        user = User.objects.create(username=username, email="primary@example.com")
        user.emailaddress_set.create(  # type: ignore[attr-defined]
            email="primary@example.com",
            primary=True,
            verified=True,
        )

        response = admin_client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES[
            "NO_PRIMARY_EMAIL_ADDRESS"
        ]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg not in response.content.decode()

    @pytest.mark.django_db()
    def test_no_warning_for_no_primary_email_address_when_non_admin(
        self,
        client: Client,
    ) -> None:
        """Test no warning for users with no primary email address.

        - When user is not admin.

        Args:
            client (Client): A general test client, not configured as an admin.
        """
        # Create a user with no primary email address
        expected_msg, response = _create_user_and_check_no_primary_email_warning(client)
        assert expected_msg not in response.content.decode()

    # Tests for when there are users whose "user" models' email address does
    # not correspond to an "accounts" email address that is both validated and
    # primary.

    def test_warning_for_users_with_mismatched_email_address(
        self,
        admin_client: Client,
    ) -> None:
        """Test that a warning is shown when users' email addresses are mismatched.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with mismatched email addresses
        username = "mismatched_email_user"
        user = User.objects.create(username=username, email="mismatch@example.com")
        user.emailaddress_set.create(  # type: ignore[attr-defined]
            email="correct@example.com",
            primary=True,
            verified=True,
        )

        response = admin_client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES["EMAIL_MISMATCH"]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg in response.content.decode()

    def test_warning_for_users_with_unverified_primary_email_address(
        self,
        admin_client: Client,
    ) -> None:
        """Test that a warning is shown.

        - When users' primary email addresses are unverified.

        Args:
            admin_client (Client): A test client with admin privileges.
        """
        # Create a user with a primary email address that is not verified
        username = "unverified_primary_email_user"
        user = User.objects.create(username=username, email="unverified@example.com")
        user.emailaddress_set.create(  # type: ignore[attr-defined]
            email="unverified@example.com",
            primary=True,
            verified=False,
        )

        response = admin_client.get("/")
        expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES[
            "NO_VERIFIED_EMAIL_ADDRESS"
        ]
        expected_msg = expected_msg_template.format(username=username)
        assert expected_msg in response.content.decode()


def _create_user_and_check_no_primary_email_warning(
    client: Client,
) -> tuple[str, HttpResponse]:
    username = "no_primary_email_user"
    user = User.objects.create(username=username, email="no_primary@example.com")
    user.emailaddress_set.create(  # type: ignore[attr-defined]
        email="no_primary@example.com",
        primary=False,
        verified=True,
    )

    response = client.get("/")
    response2 = check_type(response, HttpResponse)

    expected_msg_template = USER_EMAIL_PROBLEM_TEMPLATE_MESSAGES[
        "NO_PRIMARY_EMAIL_ADDRESS"
    ]
    expected_msg = expected_msg_template.format(username=username)
    return expected_msg, response2


@pytest.mark.django_db()
def test_maintenance_jobs_link_in_navbar_is_present_for_logged_in_agent_users(
    client: Client,
    bob_agent_user: User,
) -> None:
    """Ensure 'Maintenance Jobs' link is visible for logged-in agent users.

    Args:
        client (Client): Django's test client instance used for making requests.
        bob_agent_user (User): User instance representing Bob, an agent user.
    """
    # Log in as the agent user
    logged_in = client.login(username="bob", password=get_test_user_password())
    assert logged_in

    # Check that the "Maintenance Jobs" link is present in the navbar
    assert _maintenance_jobs_link_in_navbar_is_present(client)


@pytest.mark.django_db()
def test_maintenance_jobs_link_in_navbar_is_not_present_for_logged_out_users(
    client: Client,
) -> None:
    """Verify that 'Maintenance Jobs' link is not visible for logged-out users.

    Args:
        client (Client): Django's test client instance used for making requests.
    """
    # No users are logged in, so we don't use client.log here.
    assert not _maintenance_jobs_link_in_navbar_is_present(client)


def test_maintenance_jobs_link_in_navbar_is_not_present_for_marnie_user(
    client: Client,
    marnie_user: User,
) -> None:
    """Check 'Maintenance Jobs' link is not visible for non-agent user Marnie.

    Args:
        client (Client): Django's test client instance used for making requests.
        marnie_user (User): User instance representing Marnie, who is not an agent.
    """
    # Log in as Marnie
    logged_in = client.login(username="marnie", password=get_test_user_password())
    assert logged_in

    assert not _maintenance_jobs_link_in_navbar_is_present(client)


def test_agents_link_is_visible_for_marnie_user(
    client: Client,
    marnie_user: User,
) -> None:
    """Check that the 'Agents' link is visible for Marnie.

    Args:
        client (Client): Django's test client instance used for making requests.
        marnie_user (User): User instance representing Marnie, who is not an agent.
    """
    # Log in as Marnie
    logged_in = client.login(username="marnie", password=get_test_user_password())
    assert logged_in

    # Get the response text for visiting the home page:
    response = client.get(reverse("home"))
    response_text = response.content.decode()

    # Use BeautifulSoup to fetch the link with the text "Agents" in it:
    soup = BeautifulSoup(response_text, "html.parser")
    agents_link = soup.find("a", string="Agents")

    # It is None if not found, otherwise the link was found.
    assert agents_link is not None


def test_agents_link_is_not_visible_for_none_marnie_users(
    client: Client,
    bob_agent_user: User,
) -> None:
    """Check that the 'Agents' link is not visible for agent user Bob.

    Args:
        client (Client): Django's test client instance used for making requests.
        bob_agent_user (User): User instance representing Bob, an agent user.
    """
    # Log in as Bob
    logged_in = client.login(username="bob", password=get_test_user_password())
    assert logged_in

    # Get the response text for visiting the home page:
    response = client.get(reverse("home"))
    response_text = response.content.decode()

    # Use BeautifulSoup to fetch the link with the text "Agents" in it:
    soup = BeautifulSoup(response_text, "html.parser")
    agents_link = soup.find("a", string="Agents")

    # It is None if not found, otherwise the link was found.
    assert agents_link is None


def test_agents_link_points_to_agents_page(
    client: Client,
    marnie_user: User,
) -> None:
    """Check that the 'Agents' link points to the 'agents' page.

    Args:
        client (Client): Django's test client instance used for making requests.
        marnie_user (User): User instance representing Marnie, who is not an agent.
    """
    # Log in as Marnie
    logged_in = client.login(username="marnie", password=get_test_user_password())
    assert logged_in

    # Get the response for visiting the home page:
    response = client.get(reverse("home"))

    # Use BeautifulSoup to fetch the link with the text "Agents" in it:
    soup = BeautifulSoup(response.content.decode(), "html.parser")
    agents_link = soup.find("a", string="Agents")

    # The link should point to the 'agents' page
    assert agents_link["href"] == reverse("jobs:agent_list")


def _maintenance_jobs_link_in_navbar_is_present(client: Client) -> bool:
    # Get the response text for visiting the home page:
    response = client.get(reverse("home"))
    response_text = response.content.decode()

    # Use BeautifulSoup to fetch the link with the text "Maintenance Jobs" in it:
    soup = BeautifulSoup(response_text, "html.parser")
    maintenance_jobs_link = soup.find("a", string="Maintenance Jobs")

    # It is None if not found, otherwise the link was found.
    return maintenance_jobs_link is not None
