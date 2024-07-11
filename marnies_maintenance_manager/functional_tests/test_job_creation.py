"""Functional tests for job creation.

These tests ensure that the job creation functionalities work as expected
from a user's perspective in the Marnie's Maintenance Manager application.
"""

# pylint: disable=unused-argument

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils import _create_new_job
from marnies_maintenance_manager.users.models import User


@pytest.mark.django_db()
def test_existing_agent_user_can_login_and_create_a_new_maintenance_job_and_logout(
    browser: WebDriver,
    live_server_url: str,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """Ensure a user can log in, create a job, and log out.

    This test simulates a user logging into the system, creating a new
    maintenance job, and logging out, verifying each critical step.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        bob_agent_user (User): The user instance for Bob, who is an agent.
        marnie_user (User): The user instance for Marnie, included for context.
    """
    # The body of our logic is moved to a helper function, because we're going
    # to be re-using this logic a lot of times for other functional tests.
    _create_new_job(browser, live_server_url)
