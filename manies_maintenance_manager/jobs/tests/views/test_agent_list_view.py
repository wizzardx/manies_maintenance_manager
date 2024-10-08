"""Unit tests for the Agent List view."""

# pylint: disable=magic-value-comparison,unused-argument

import bs4
import pytest
from bs4 import BeautifulSoup
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from manies_maintenance_manager.users.models import User


def test_manie_can_reach_agents_view(manie_user_client: Client) -> None:
    """Ensure Manie can access the agents view.

    Args:
        manie_user_client (Client): A test client for Manie.
    """
    response = manie_user_client.get(reverse("jobs:agent_list"))
    assert response.status_code == status.HTTP_200_OK


def test_superuser_can_reach_agents_view(superuser_client: Client) -> None:
    """Ensure superusers can access the agents view.

    Args:
        superuser_client (Client): A test client for a superuser.
    """
    response = superuser_client.get(reverse("jobs:agent_list"))
    assert response.status_code == status.HTTP_200_OK


def test_none_manie_user_cannot_reach_agents_view(
    bob_agent_user_client: Client,
) -> None:
    """Ensure non-Manie users cannot access the agents view.

    Args:
        bob_agent_user_client (Client): A test client for Bob, an agent user.
    """
    response = bob_agent_user_client.get(reverse("jobs:agent_list"))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db()
def test_anonymous_user_cannot_reach_agents_view(client: Client) -> None:
    """Ensure anonymous users cannot access the agents view.

    Args:
        client (Client): A test client for an anonymous user.
    """
    response = client.get(reverse("jobs:agent_list"))
    assert response.status_code == status.HTTP_302_FOUND
    response2 = check_type(response, HttpResponseRedirect)
    assert response2.url == "/accounts/login/?next=/jobs/agents/"


def test_agents_view_contains_agent_list(
    manie_user_client: Client,
    bob_agent_user: User,
    admin_user: User,
) -> None:
    """Ensure the agents view contains a list of agents.

    Args:
        manie_user_client (Client): A test client for Manie.
        bob_agent_user (User): Bob's user instance, an agent.
        admin_user (User): Admin user instance, not an agent.
    """
    list_items = _get_agent_list_items(manie_user_client)
    agent_usernames = [li.a.string for li in list_items]

    # Bob is an Agent, so his username should be in the list.
    assert bob_agent_user.username in agent_usernames

    # Admin is not an Agent, so despite being a user, his username should not be in
    # the list.
    assert admin_user.username not in agent_usernames


def test_agent_names_are_links_to_their_created_maintenance_jobs(
    manie_user_client: Client,
    bob_agent_user: User,
) -> None:
    """Ensure agent names are links to their created maintenance jobs.

    Args:
        manie_user_client (Client): A test client for Manie.
        bob_agent_user (User): Bob's user instance, an agent.
    """
    list_items = _get_agent_list_items(manie_user_client)

    # There should be exactly one of them:
    assert len(list_items) == 1

    # The list item should be a link.
    assert list_items[0].a is not None

    # The link text should be the agent's username.
    assert list_items[0].a.string == bob_agent_user.username

    # The link URL should point to the correct location where we can
    # find the maintenance jobs that were created by this Agent:
    assert (
        list_items[0].a["href"]
        == reverse("jobs:job_list") + f"?agent={bob_agent_user.username}"
    )


def _get_agent_list_items(manie_user_client: Client) -> bs4.element.ResultSet:
    response = manie_user_client.get(reverse("jobs:agent_list"))
    assert response.status_code == status.HTTP_200_OK

    page_text = response.content.decode()

    # Use beautifulsoup to find the <ul> element with ID "agent_list":
    soup = BeautifulSoup(page_text, "html.parser")
    agent_list = soup.find("ul", id="agent_list")
    assert agent_list is not None

    # Grab the LI elements from there:
    return agent_list.find_all("li")


def test_agents_are_listed_in_alphanumeric_order_by_username(
    manie_user_client: Client,
    alice_agent_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure agents are listed in alphanumeric order by username.

    Args:
        manie_user_client (Client): A test client for Manie.
        alice_agent_user (User): Alice's user instance, an agent.
        bob_agent_user (User): Bob's user instance, an agent.
    """
    list_items = _get_agent_list_items(manie_user_client)
    agent_usernames = [li.a.string for li in list_items]

    # Bob should come after Alice, since "bob" comes after "alice" in
    # alphanumeric order.
    assert agent_usernames == sorted(agent_usernames)
