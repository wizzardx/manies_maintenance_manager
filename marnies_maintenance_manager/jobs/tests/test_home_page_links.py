"""Tests for the home page link visibility on Marnie's Maintenance Manager site.

This module contains tests that verify the presence or absence of specific
navigation links on the home page based on user authentication and roles.
"""

# pylint: disable=unused-argument

import pytest
from bs4 import BeautifulSoup
from django.test.client import Client
from django.urls import reverse

from marnies_maintenance_manager.users.models import User


def _maintenance_jobs_link_in_navbar_is_present(client: Client) -> bool:
    # Get the response text for visiting the home page:
    response = client.get(reverse("home"))
    response_text = response.content.decode()

    # Use BeautifulSoup to fetch the link with the text "Maintenance Jobs" in it:
    soup = BeautifulSoup(response_text, "html.parser")
    maintenance_jobs_link = soup.find("a", string="Maintenance Jobs")

    # It is None if not found, otherwise the link was found.
    return maintenance_jobs_link is not None


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
    logged_in = client.login(username="bob", password="password")  # noqa: S106
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
    logged_in = client.login(username="marnie", password="password")  # noqa: S106
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
    logged_in = client.login(username="marnie", password="password")  # noqa: S106
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
    logged_in = client.login(username="bob", password="password")  # noqa: S106
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
    logged_in = client.login(username="marnie", password="password")  # noqa: S106
    assert logged_in

    # Get the response for visiting the home page:
    response = client.get(reverse("home"))

    # Use BeautifulSoup to fetch the link with the text "Agents" in it:
    soup = BeautifulSoup(response.content.decode(), "html.parser")
    agents_link = soup.find("a", string="Agents")

    # The link should point to the 'agents' page
    assert agents_link["href"] == reverse("jobs:agent_list")
