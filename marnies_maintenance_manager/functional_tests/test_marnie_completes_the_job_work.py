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

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from typeguard import check_type

from marnies_maintenance_manager.functional_tests.utils import (
    _bob_accepts_marnies_quote,
)
from marnies_maintenance_manager.functional_tests.utils import _bob_submits_deposit_pop
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

from .utils import _check_maintenance_jobs_page_table_after_job_completion


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

    # Bob logs out
    _sign_out_of_website_and_clean_up(browser)

    # Marnie logs in and goes to the job details.
    _sign_in_as_marie_and_navigate_to_job_details(browser)

    # He can see an "Update" link at the bottom of the page.
    update_link = browser.find_element(By.LINK_TEXT, "Update")

    # He clicks on the "Update" link.
    update_link.click()

    # He is taken to a "Complete the Job" page. He can see that title both
    # in the browser tab and on the page itself as its heading.
    assert "Complete the Job" in browser.title
    heading = browser.find_element(By.TAG_NAME, "h1")
    assert "Complete the Job" in heading.text

    # He sees a field where he can input the Job (completion) Date:
    job_date_input = browser.find_element(By.NAME, "job_date")
    assert job_date_input is not None

    # He enters the job completion date:
    job_date_input.send_keys("03022021")

    # He sees a field where he can input comments on the job.
    comments_input = browser.find_element(By.NAME, "comments")
    assert comments_input is not None

    # He types in some comments:
    comments_input.send_keys(
        "I fixed the leaky faucet\n"
        "While I was in there I noticed damage in the wall\n"
        "Do you want me to fix that too?",
    )

    # He sees a field where he can upload an invoice for the work done:
    invoice_input = browser.find_element(By.NAME, "invoice")
    assert invoice_input is not None

    # He uploads the invoice file:
    invoice_input.send_keys(
        "/app/marnies_maintenance_manager/functional_tests/test.pdf",
    )

    # He sees a "Submit" button and clicks it:
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    submit_button.click()

    # He is taken back to the maintenance jobs page for Bob.
    assert browser.title == "Maintenance Jobs for bob"
    assert browser.find_element(By.TAG_NAME, "h1").text == "Maintenance Jobs for bob"

    # He sees a flash notification that the job has been completed.
    expected_msg = "The job has been completed. An email has been sent to bob."
    assert expected_msg in browser.page_source

    # He checks the job-listing page in detail, that his there and in the expected
    # state.
    _check_maintenance_jobs_page_table_after_job_completion(browser)

    # He clicks on the job number link to view the job details.
    job_number_link = browser.find_element(By.LINK_TEXT, "1")
    job_number_link.click()

    # He is taken back to the job details page.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees the link to the invoice he uploaded, with the text "Download Invoice",
    # and with a realistic-looking URL:
    invoice_link = browser.find_element(By.LINK_TEXT, "Download Invoice")
    assert invoice_link is not None
    assert "Download Invoice" in invoice_link.text
    assert "test.pdf" in check_type(invoice_link.get_attribute("href"), str)

    # He sees the comments he entered earlier:
    comments = browser.find_element(By.CLASS_NAME, "comments")
    assert comments is not None
    assert "I fixed the leaky faucet" in comments.text
    assert "While I was in there I noticed damage in the wall" in comments.text
    assert "Do you want me to fix that too?" in comments.text

    # He sees the job completion date he entered earlier:
    job_date = browser.find_element(By.CLASS_NAME, "job-date")
    assert job_date is not None
    assert "2021-03-02" in job_date.text

    # He sees the link to the invoice he uploaded earlier:
    invoice_link = browser.find_element(By.LINK_TEXT, "Download Invoice")
    assert invoice_link is not None
    assert "Download Invoice" in invoice_link.text

    # Happy with this, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)
