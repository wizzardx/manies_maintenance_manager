"""Unit tests for the Agent List view."""

# pylint: disable=no-self-use

from typing import cast

import pytest
from bs4 import BeautifulSoup
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.users.models import User


class TestAgentsView:
    """Test the Agents view in the Jobs app."""

    def test_marnie_can_reach_agents_view(self, marnie_user_client: Client) -> None:
        """Ensure Marnie can access the agents view.

        Args:
            marnie_user_client (Client): A test client for Marnie.
        """
        response = marnie_user_client.get(reverse("jobs:agent_list"))
        assert response.status_code == status.HTTP_200_OK

    def test_superuser_can_reach_agents_view(self, superuser_client: Client) -> None:
        """Ensure superusers can access the agents view.

        Args:
            superuser_client (Client): A test client for a superuser.
        """
        response = superuser_client.get(reverse("jobs:agent_list"))
        assert response.status_code == status.HTTP_200_OK

    def test_none_marnie_user_cannot_reach_agents_view(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure non-Marnie users cannot access the agents view.

        Args:
            bob_agent_user_client (Client): A test client for Bob, an agent user.
        """
        response = bob_agent_user_client.get(reverse("jobs:agent_list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db()
    def test_anonymous_user_cannot_reach_agents_view(self, client: Client) -> None:
        """Ensure anonymous users cannot access the agents view.

        Args:
            client (Client): A test client for an anonymous user.
        """
        response = client.get(reverse("jobs:agent_list"))
        assert response.status_code == status.HTTP_302_FOUND
        response2 = cast(HttpResponseRedirect, response)
        assert response2.url == "/accounts/login/?next=/jobs/agents/"

    def test_agents_view_contains_agent_list(
        self,
        marnie_user_client: Client,
        bob_agent_user: User,
        admin_user: User,
    ) -> None:
        """Ensure the agents view contains a list of agents.

        Args:
            marnie_user_client (Client): A test client for Marnie.
            bob_agent_user (User): Bob's user instance, an agent.
            admin_user (User): Admin user instance, not an agent.
        """
        response = marnie_user_client.get(reverse("jobs:agent_list"))
        assert response.status_code == status.HTTP_200_OK

        # Bob is an Agent, so his username should be in the list.
        page_text = response.content.decode()
        assert bob_agent_user.username in page_text

        # Admin is not an Agent, so despite being a user, his username should not be in
        # the list.
        assert User.objects.filter(username=admin_user.username).exists()
        assert admin_user.username not in page_text

    def test_agent_names_are_links_to_their_created_maintenance_jobs(
        self,
        marnie_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Ensure agent names are links to their created maintenance jobs.

        Args:
            marnie_user_client (Client): A test client for Marnie.
            bob_agent_user (User): Bob's user instance, an agent.
        """
        response = marnie_user_client.get(reverse("jobs:agent_list"))
        assert response.status_code == status.HTTP_200_OK

        page_text = response.content.decode()

        # Use beautifulsoup to find the <ul> element with ID "agent_list":
        soup = BeautifulSoup(page_text, "html.parser")
        agent_list = soup.find("ul", id="agent_list")
        assert agent_list is not None

        # Grab the LI elements from there:
        list_items = agent_list.find_all("li")

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
