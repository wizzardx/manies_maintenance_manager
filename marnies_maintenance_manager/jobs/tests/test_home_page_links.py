"""Tests for the home page link visibility on Marnie's Maintenance Manager site.

This module contains tests that verify the presence or absence of specific
navigation links on the home page based on user authentication and roles.
"""

import pytest
from bs4 import BeautifulSoup
from django.test.client import Client

from marnies_maintenance_manager.users.models import User


def _maintenance_jobs_link_in_navbar_is_present(client: Client) -> bool:
    # Get the response text for visiting the home page:
    response = client.get("/")
    response_text = response.content.decode()

    # Use BeautifulSup to fetch the link with the text "Maintenance Jobs" in it:
    soup = BeautifulSoup(response_text, "html.parser")
    maintenance_jobs_link = soup.find("a", string="Maintenance Jobs")

    # It is None if not found, otherwise the link was found.
    return maintenance_jobs_link is not None


@pytest.mark.django_db()
def test_maintenance_jobs_link_in_navbar_is_present_for_logged_in_agent_users(
    client: Client,
    bob_agent_user: User,
) -> None:
    """Ensure 'Maintenance Jobs' link is visible for logged-in agent users."""
    # Log in as the agent user
    logged_in = client.login(username="bob", password="password")  # noqa: S106
    assert logged_in

    # Check that the "Maintenance Jobs" link is present in the navbar
    assert _maintenance_jobs_link_in_navbar_is_present(client)


@pytest.mark.django_db()
def test_maintenance_jobs_link_in_navbar_is_not_present_for_logged_out_users(
    client: Client,
) -> None:
    """Verify that 'Maintenance Jobs' link is not visible for logged-out users."""
    # No users are logged in, so we don't use client.log here.
    assert not _maintenance_jobs_link_in_navbar_is_present(client)


def test_maintenance_jobs_link_in_navbar_is_not_present_for_marnie_user(
    client: Client,
    marnie_user: User,
) -> None:
    """Check 'Maintenance Jobs' link is not visible for non-agent user Marnie."""
    # Log in as Marnie
    logged_in = client.login(username="marnie", password="password")  # noqa: S106
    assert logged_in

    assert not _maintenance_jobs_link_in_navbar_is_present(client)
