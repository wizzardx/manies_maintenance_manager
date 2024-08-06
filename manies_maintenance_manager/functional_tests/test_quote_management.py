"""Functional tests for quote management.

These tests ensure that the quote management functionalities, including
accepting, rejecting, and resubmitting quotes, work as expected from a user's
perspective in the Manie's Maintenance Manager application.
"""

# pylint: disable=unused-argument, magic-value-comparison

from pathlib import Path

import environ
import requests
from rest_framework import status
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _bob_accepts_manies_quote,
)
from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _bob_rejects_manies_quote,
)
from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _create_new_job,
)
from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _update_job_with_inspection_date_and_quote,
)
from manies_maintenance_manager.functional_tests.utils.login import (
    _sign_out_of_website_and_clean_up,
)
from manies_maintenance_manager.functional_tests.utils.navigation import (
    _sign_in_as_manie_and_navigate_to_job_details,
)
from manies_maintenance_manager.users.models import User

FUNCTIONAL_TESTS_DATA_DIR = Path(__file__).resolve().parent

env = environ.Env()


def test_bob_can_reject_manies_quote(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Bob can reject the quote submitted by Manie.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        manie_user (User): The user instance for Manie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Manie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    ## Bob Rejects Manies quote:
    _bob_rejects_manies_quote(browser)


def test_bob_can_accept_manies_quote(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Bob can accept the quote submitted by Manie.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        manie_user (User): The user instance for Manie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Manie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    # The rest of the logic, moved over to his shared function:
    _bob_accepts_manies_quote(browser)

    # Happy with this so far, but not yet ready to upload a proof of payment,
    # he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


def test_after_rejection_manie_can_resubmit_quote(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Manie can resubmit a quote after it has been rejected by Bob.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        manie_user (User): The user instance for Manie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Manie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    ## Bob rejects the quote.
    _bob_rejects_manies_quote(browser)

    # Manie logs into the system and navigates through to the detail page of the job
    _sign_in_as_manie_and_navigate_to_job_details(browser)

    # He sees the link to his previously uploaded file for the quote:
    quote_link = browser.find_element(By.LINK_TEXT, "Download Quote")
    assert quote_link is not None

    # He sees an "Upload new Quote" link, and clicks on it.
    update_quote_link = browser.find_element(By.LINK_TEXT, "Upload new Quote")
    update_quote_link.click()

    # He sees the "Update Quote" page, with the title and header mentioning the same.
    assert "Update Quote" in browser.title
    assert "Update Quote" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees the "Quote" field, and a "Submit" button.
    quote_invoice_field = browser.find_element(By.ID, "id_quote")
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He uploads a new Quote invoice.
    quote_invoice_field.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test_2.pdf"))

    # He clicks the "submit" button.
    submit_button.click()

    # This takes him back to the details page for the Job.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a flash notification that an email has been sent to Bob.
    expected_msg = (
        "Your updated quote has been uploaded. An email has been sent to bob."
    )
    assert expected_msg in browser.page_source

    # Satisfied, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


def test_anonymous_user_cannot_download_uploaded_quote_file(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure an anonymous user cannot download an uploaded quote file.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        manie_user (User): The user instance for Manie.
        bob_agent_user (User): The user instance for Bob, who is an agent
    """
    ## Run through our shared workflow that starts with a new job and then
    ## takes it all the way through to Manie having done the work and assigned
    ## an invoice.
    _create_new_job(browser, live_server_url)

    ## Next, Manie does an inspection, and updates the inspection date and quote.
    info = _update_job_with_inspection_date_and_quote(browser)

    ## Grab the quote download URL:
    quote_download_url = info["quote_download_url"]

    ## Check the download link (this should fail):
    response = requests.head(quote_download_url, timeout=5)
    assert response.status_code == status.HTTP_403_FORBIDDEN
