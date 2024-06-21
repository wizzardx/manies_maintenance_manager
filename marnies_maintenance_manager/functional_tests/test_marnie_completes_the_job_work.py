"""Test for Completing a Job and Uploading an Invoice in Marnie's Maintenance Manager.

This module contains a functional test that verifies Marnie can complete a job and
upload an invoice for it using the Selenium WebDriver.

Workflow:
1. Create a new job as an agent.
2. Marnie updates the job with an inspection date and quote.
3. Bob accepts the quote and submits a proof of payment for the deposit.
4. Marnie completes the job, inputs the completion date, adds comments, and uploads an
   invoice.
5. The system verifies all steps are completed successfully, including viewing the job
details and associated documents.

Imports:
    - date: To handle the job completion date.
    - WebDriver, By: From selenium.webdriver for browser automation.
    - Utility functions from marnies_maintenance_manager.functional_tests.utils.
    - User model from marnies_maintenance_manager.users.models.

Usage:
    This test is designed to be run as part of a larger test suite to ensure the
    functionality of job completion and invoice management in the Marnie's Maintenance
    Manager application.

Note:
    Pylint warnings for unused arguments and magic value comparison are disabled.
"""

# pylint: disable=unused-argument, magic-value-comparison, too-many-statements
# pylint: disable=too-many-locals
# ruff: noqa: PLR0915

from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils import (
    _bob_accepts_marnies_quote,
)
from marnies_maintenance_manager.functional_tests.utils import _bob_submits_deposit_pop
from marnies_maintenance_manager.functional_tests.utils import _create_new_job
from marnies_maintenance_manager.functional_tests.utils import _marnie_completes_the_job
from marnies_maintenance_manager.functional_tests.utils import (
    _update_job_with_inspection_date_and_quote,
)
from marnies_maintenance_manager.users.models import User


def test_marnie_completes_the_job(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Test that Marnie can complete a job and upload an invoice for it.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    # Let's run through the previous steps first, to get to the point where Marnie
    # can complete the job:

    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Marnie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    ## After this, quickly accept the quote:
    _bob_accepts_marnies_quote(browser)

    # And then, Bob submits the Deposit Proof of Payment:
    _bob_submits_deposit_pop(browser)

    ## The next part has been moved over to a shared function:
    _marnie_completes_the_job(browser)
