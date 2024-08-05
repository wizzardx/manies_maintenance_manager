"""Utility functions for simulating complete user workflows in functional tests.

This module contains functions that string together multiple actions to simulate
entire user journeys, from job creation to completion, including interactions
from both the client and contractor perspectives.
"""

# pylint: disable=magic-value-comparison,too-many-locals

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .constants import FUNCTIONAL_TESTS_DATA_DIR
from .job_creation import _bob_accepts_marnies_quote
from .job_creation import _bob_submits_deposit_pop
from .job_creation import _create_new_job
from .job_creation import _marnie_does_onsite_work_then_uploads_his_final_docs
from .job_creation import _update_job_with_inspection_date_and_quote
from .login import _sign_into_website
from .login import _sign_out_of_website_and_clean_up
from .page_checks import (
    _check_maintenance_jobs_page_table_after_final_payment_pop_submission,
)


def _workflow_from_new_job_to_completed_by_marnie(
    browser: WebDriver,
    live_server_url: str,
) -> None:
    """Run through the initial job workflow steps.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
    """
    ## Run through our shared workflow that starts with a new job and then
    ## takes it all the way through to Marnie having done the work and assigned
    ## an invoice.
    _create_new_job(browser, live_server_url)

    ## Next, Marnie does an inspection, and updates the inspection date and quote.
    _update_job_with_inspection_date_and_quote(browser)

    ## After this, quickly accept the quote:
    _bob_accepts_marnies_quote(browser)

    ## And then, Bob submits the Deposit Proof of Payment:
    _bob_submits_deposit_pop(browser)

    ## After that, Marnie completes the job and uploads a final invoice.
    _marnie_does_onsite_work_then_uploads_his_final_docs(browser)


def _workflow_from_new_job_to_final_pop_added_by_bob(
    browser: WebDriver,
    live_server_url: str,
) -> None:
    # Let's run through the previous steps first, to get to the point where our agent
    # Bob can upload the final payment proof of payment:
    _workflow_from_new_job_to_completed_by_marnie(browser, live_server_url)

    # We're all caught up now. We can start the user story now.

    # Bob logs in now.
    _sign_into_website(browser, "bob")

    # Then he goes to the Maintenance Jobs page:
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # He sees the details of the job, and clicks on the number to view the details:

    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be exactly one row here
    assert len(rows) == 2  # noqa: PLR2004

    ## Get the row, and confirm that the details include everything submitted up until
    ## now.
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
    expected = [
        "1",
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",
        "Download Quote",
        "A",  # Accept or Reject A/R
        "Download POP",  # Deposit POP
        "2021-03-02",  # Job Date
        "Download Photo 1 Download Photo 2",  # Job Photos
        "Download Invoice",  # Invoice
        "I fixed the leaky faucet While I was in there I noticed damage in the "
        "wall Do you want me to fix that too?",  # Comments
        "",  # Final Payment POP
        "No",  # Job Complete
    ]
    assert cell_texts == expected

    # He clicks on the #1 number again:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()

    # He sees the "Upload Final Payment POP" link, and clicks on it.
    upload_final_pop_link = browser.find_element(
        By.LINK_TEXT,
        "Upload Final Payment POP",
    )
    upload_final_pop_link.click()

    # He can see the new title and header for the page.
    assert "Upload Final Payment Proof of Payment" in browser.title
    header = browser.find_element(By.TAG_NAME, "h1")
    assert "Upload Final Payment Proof of Payment" in header.text

    # He sees a form with a file input field, and a "submit" button.
    file_input = browser.find_element(By.ID, "id_final_payment_pop")
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He uploads the final payment proof of payment.
    file_input.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test.pdf"))

    # He clicks the "submit" button.
    submit_button.click()

    # This takes him back to the Job Details page.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a popup message informing him that the final payment proof of payment
    # has been submitted successfully, and that Marnie has been emailed.
    expected_message = (
        "Your Final Payment Proof of Payment has been uploaded. "
        "An email has been sent to Marnie."
    )
    assert expected_message in browser.page_source

    # Over in the job details page he can see the link to his previously uploaded file,
    # with the text "Download Deposit POP":
    pop_link_elem = browser.find_element(
        By.LINK_TEXT,
        "Download Final Payment POP",
    )  # FT reaches this point so far
    assert pop_link_elem is not None

    # He also wants to see the job-listing page, so he clicks the "Maintenance Jobs"
    # link in the NavBar:
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # He sees the table with the job details, and the final "proof of payment"
    # link in the table.
    _check_maintenance_jobs_page_table_after_final_payment_pop_submission(
        browser,
    )

    # Happy with this, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)
