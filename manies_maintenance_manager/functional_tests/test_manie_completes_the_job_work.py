"""Test for Completing a Job and Uploading an Invoice in Manie's Maintenance Manager.

This module contains a functional test that verifies Manie can complete a job and
upload an invoice for it using the Selenium WebDriver.

Workflow:
1. Create a new job as an agent.
2. Manie updates the job with an inspection date and quote.
3. Bob accepts the quote and submits a proof of payment for the deposit.
4. Manie completes the job, inputs the completion date, adds comments, and uploads an
   invoice.
5. The system verifies all steps are completed successfully, including viewing the job
details and associated documents.

Imports:
    - date: To handle the job completion date.
    - WebDriver, By: From selenium.webdriver for browser automation.
    - Utility functions from manies_maintenance_manager.functional_tests.utils.
    - User model from manies_maintenance_manager.users.models.

Usage:
    This test is designed to be run as part of a larger test suite to ensure the
    functionality of job completion and invoice management in the Manie's Maintenance
    Manager application.

Note:
    Pylint warnings for unused arguments and magic value comparison are disabled.
"""

# pylint: disable=unused-argument, magic-value-comparison, too-many-statements
# pylint: disable=too-many-locals
# ruff: noqa: PLR0915

from selenium.webdriver.remote.webdriver import WebDriver

from manies_maintenance_manager.functional_tests.utils.workflows import (
    _workflow_from_new_job_to_completed_by_manie,
)
from manies_maintenance_manager.users.models import User


def test_manie_completes_the_job(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Test that Manie can complete a job and upload an invoice for it.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        manie_user (User): The user instance for Manie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## Run through our shared workflow that starts with a new job and then
    ## takes it all the way through to Manie having done the work and assigned
    ## an invoice.
    _workflow_from_new_job_to_completed_by_manie(browser, live_server_url)
