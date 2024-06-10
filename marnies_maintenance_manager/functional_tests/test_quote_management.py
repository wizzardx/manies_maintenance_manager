"""Functional tests for quote management.

These tests ensure that the quote management functionalities, including
accepting, rejecting, and resubmitting quotes, work as expected from a user's
perspective in the Marnie's Maintenance Manager application.
"""

# pylint: disable=unused-argument, magic-value-comparison

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils import (
    _bob_accepts_marnies_quote,
)
from marnies_maintenance_manager.functional_tests.utils import (
    _bob_rejects_marnies_quote,
)
from marnies_maintenance_manager.functional_tests.utils import _create_new_job
from marnies_maintenance_manager.functional_tests.utils import (
    _sign_in_as_marie_and_navigate_to_job_details,
)
from marnies_maintenance_manager.functional_tests.utils import (
    _sign_out_of_website_and_clean_up,
)
from marnies_maintenance_manager.functional_tests.utils import (
    _update_job_with_inspection_date_and_quote,
)
from marnies_maintenance_manager.users.models import User


def test_bob_can_reject_marnies_quote(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Bob can reject the quote submitted by Marnie.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Marnie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    ## Bob Rejects Marnies quote:
    _bob_rejects_marnies_quote(browser)


def test_bob_can_accept_marnies_quote(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Bob can accept the quote submitted by Marnie.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Marnie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    # The rest of the logic, moved over to his shared function:
    _bob_accepts_marnies_quote(browser)

    # Happy with this so far, but not yet ready to upload a proof of payment,
    # he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


def test_after_rejection_marnie_can_resubmit_quote(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Marnie can resubmit a quote after it has been rejected by Bob.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    ## First, quickly run through the steps of an Agent creating a new Job.
    _create_new_job(browser, live_server_url)

    ## Next, Marnie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    ## Bob rejects the quote.
    _bob_rejects_marnies_quote(browser)

    # Marnie logs into the system and navigates through to the detail page of the job
    _sign_in_as_marie_and_navigate_to_job_details(browser)

    # He sees the link to his previously uploaded file for the quote:
    quote_link = browser.find_element(By.LINK_TEXT, "Download Quote")
    assert quote_link is not None

    # He sees an "Update Quote" link, and clicks on it.
    update_quote_link = browser.find_element(By.LINK_TEXT, "Update Quote")
    update_quote_link.click()

    # He sees the "Update Quote" page, with the title and header mentioning the same.
    assert "Update Quote" in browser.title
    assert "Update Quote" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees the "Quote" field, and a "Submit" button.
    quote_invoice_field = browser.find_element(By.ID, "id_quote")
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He uploads a new Quote invoice.
    quote_invoice_field.send_keys(
        "/app/marnies_maintenance_manager/functional_tests/test_2.pdf",
    )

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
