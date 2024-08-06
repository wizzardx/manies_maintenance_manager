"""Test user story: Agent uploads final payment proof of payment."""

# pylint: disable=magic-value-comparison,unused-argument,disable=too-many-locals

from pathlib import Path

import environ
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils.workflows import (
    _workflow_from_new_job_to_final_pop_added_by_bob,
)
from marnies_maintenance_manager.users.models import User

env = environ.Env()

FUNCTIONAL_TESTS_DATA_DIR = Path(__file__).resolve().parent


def test_agent_uploads_final_payment_pop(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Test that Bob can upload the final payment proof of payment.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    # Our workflow here is reused in other places, so we've abstracted it into
    # another function, which we'll call here:
    _workflow_from_new_job_to_final_pop_added_by_bob(browser, live_server_url)
