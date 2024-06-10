"""Functional tests for payment proof submission.

These tests ensure that the functionalities related to submitting proof of
payment work as expected from a user's perspective in the Marnie's Maintenance
Manager application.
"""

# pylint: disable=unused-argument, magic-value-comparison

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils import (
    _bob_accepts_marnies_quote,
)
from marnies_maintenance_manager.functional_tests.utils import _create_new_job
from marnies_maintenance_manager.functional_tests.utils import (
    _sign_out_of_website_and_clean_up,
)
from marnies_maintenance_manager.functional_tests.utils import (
    _update_job_with_inspection_date_and_quote,
)
from marnies_maintenance_manager.users.models import User


def test_agent_can_submit_deposit_pop_after_accepting_marnie_quote(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Bob can submit proof of payment after accepting Marnie's quote.

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

    ## After this, quickly accept the quote:
    _bob_accepts_marnies_quote(browser)

    ## At this point, Bob should still be logged into the system, and the current page
    ## should be the "Maintenance Job Details" page. Confirm that:
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a "Submit Deposit POP" link, and clicks on it.
    submit_pop_link = browser.find_element(
        By.LINK_TEXT,
        "Submit Deposit Proof of Payment",
    )
    submit_pop_link.click()

    # He sees the "Submit Deposit POP" page, with the title and header mentioning the
    # same.
    assert "Submit Deposit POP" in browser.title
    assert "Submit Deposit POP" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees the "Proof of Payment" field, and a "Submit" button.
    pop_field = browser.find_element(By.ID, "id_deposit_proof_of_payment")
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He uploads a Proof of Payment.
    pop_field.send_keys(
        "/app/marnies_maintenance_manager/functional_tests/test.pdf",
    )

    # He clicks the "submit" button.
    submit_button.click()

    # This takes him back to the details page for the Job.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a flash notification that an email has been sent to Marnie.
    expected_msg = (
        "Your Deposit Proof of Payment has been uploaded. An email has "
        "been sent to Marnie."
    )
    assert expected_msg in browser.page_source

    # Happy with this, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)
