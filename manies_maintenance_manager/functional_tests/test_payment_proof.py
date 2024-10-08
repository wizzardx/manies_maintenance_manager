"""Functional tests for payment proof submission.

These tests ensure that the functionalities related to submitting proof of
payment work as expected from a user's perspective in the Manie's Maintenance
Manager application.
"""

# pylint: disable=unused-argument, magic-value-comparison

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _bob_accepts_manies_quote,
)
from manies_maintenance_manager.functional_tests.utils.job_creation import (
    _bob_submits_deposit_pop,
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
    _manie_logs_in_and_navigates_to_bob_jobs,
)
from manies_maintenance_manager.functional_tests.utils.page_checks import (
    _check_maintenance_jobs_table,
)
from manies_maintenance_manager.users.models import User


def _check_maintenance_jobs_page_table_after_pop_submission(browser: WebDriver) -> None:
    # He notices that the new Maintenance Job is listed on the web page in a table
    cell_texts = _check_maintenance_jobs_table(browser)["cell_texts"]

    ## Make sure the cell text contents match the expected values.
    assert cell_texts == [
        "1",  # This is for the row number, automatically added by the system.
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",  # This is the displayed text, on-screen it's a link
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",  # Date of Inspection
        "Download Quote",  # Quote
        "A",  # Accept or Reject A/R
        "Download POP",  # Deposit POP
        "",  # Invoice
        "",  # Job Date
        "",  # Job Completion Photos
        "",  # Comments on the job
        "",  # Final Payment POP
        "No",  # Job Complete
    ]


def test_agent_can_submit_deposit_pop_after_accepting_manie_quote(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Bob can submit proof of payment after accepting Manie's quote.

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

    ## After this, quickly accept the quote:
    _bob_accepts_manies_quote(browser)

    ## And then he can submit the Deposit Proof of Payment:
    _bob_submits_deposit_pop(browser)

    # After submitting the POP, he goes back to the job listing page.
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # This sends him to the "Maintenance Jobs" page, where he notices that the page
    # title and the header mention Jobs
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    ## Thoroughly check that the table has the correct headings and row contents.
    _check_maintenance_jobs_page_table_after_pop_submission(browser)

    # Happy with this, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


def test_manie_can_see_deposit_pop_after_bob_submits_it(
    browser: WebDriver,
    live_server_url: str,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure Manie can see the deposit proof of payment after Bob submits it.

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

    ## After this, quickly accept the quote:
    _bob_accepts_manies_quote(browser)

    # And then, Bob submits the Deposit Proof of Payment:
    _bob_submits_deposit_pop(browser)

    # Bob logs out
    _sign_out_of_website_and_clean_up(browser)

    # Manie logs in, and navigates to Bob's jobs page
    _manie_logs_in_and_navigates_to_bob_jobs(browser)

    # He sees the title for the Bobs jobs page:
    assert "Maintenance Jobs for bob" in browser.title

    # Over there, he can see all the details for a new job:
    _check_maintenance_jobs_page_table_after_pop_submission(browser)

    # He clicks on the job's number field to see the details.
    job_number_link = browser.find_element(By.LINK_TEXT, "1")
    job_number_link.click()

    # He can see the link to the Deposit POP:
    pop_link_elem = browser.find_element(By.LINK_TEXT, "Download Deposit POP")
    assert pop_link_elem is not None

    # Happy with this, Manie logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)
