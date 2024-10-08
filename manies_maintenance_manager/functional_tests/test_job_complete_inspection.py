"""Functional tests for job updates.

These tests ensure that the job update functionalities, including modifying
job details and updating inspection dates and quotes, work as expected from
a user's perspective in the Manie's Maintenance Manager application.
"""

# pylint: disable=unused-argument, magic-value-comparison

from selenium.webdriver.remote.webdriver import WebDriver

from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _create_new_job,
)
from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _update_job_with_inspection_date_and_quote,
)
from manies_maintenance_manager.users.models import User


def test_manie_can_update_agents_job(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Manie can update the details of a job submitted by Bob the Agent.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        manie_user (User): The user instance for Manie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    # Most of our logic is now in this shared function:
    _update_job_with_inspection_date_and_quote(browser)
