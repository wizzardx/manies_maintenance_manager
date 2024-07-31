"""Helper functions for functional tests.

This module contains utility functions and fixtures used across various
functional test modules for the Marnie's Maintenance Manager application.
These utilities include common actions such as signing in and out of the
application, waiting for certain conditions, and creating or updating
job entries.
"""

# pylint: disable=unused-argument, magic-value-comparison, too-many-locals
# pylint: disable=too-many-statements, disable=consider-using-assignment-expr
# ruff: noqa: ERA001, PLR0915

import datetime
import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import environ
import pytest
from selenium.common import ElementClickInterceptedException
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from typeguard import check_type

from marnies_maintenance_manager.jobs.tests.utils import (
    suppress_fastdev_strict_if_deprecation_warning,
)
from marnies_maintenance_manager.jobs.utils import get_test_user_password

env = environ.Env()

MAX_WAIT = 5  # Maximum time to wait during retries, before failing the test

FUNCTIONAL_TESTS_DATA_DIR = Path(__file__).resolve().parent


def get_date_format_from_locale() -> str:
    """Get the date format from the system locale settings.

    Returns:
        str: The date format string.

    Raises:
        RuntimeError: If an error occurs while running the locale command.
        ValueError: If the date format cannot be determined from the locale settings.
    """
    # Run the `locale -k LC_TIME` command
    result = subprocess.run(  # noqa: S603
        ["locale", "-k", "LC_TIME"],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )

    # Check for errors
    if result.returncode != 0:
        msg = f"Error running locale command: {result.stderr}"
        raise RuntimeError(msg)

    # Parse the output to find the date format
    output = result.stdout
    date_format = None

    # Look for the d_fmt line which specifies the date format

    # pylint: disable=consider-using-assignment-expr
    match = re.search(r'd_fmt="([^"]+)"', output)
    if match:
        date_format = match.group(1)

    if not date_format:
        msg = "Unable to determine date format from locale settings"
        raise ValueError(msg)

    return date_format


def get_crispy_forms_date_input_format() -> str:
    """Get the date input format used by Crispy Forms.

    Returns:
        str: The date input format string.
    """
    # pylint: disable=consider-using-assignment-expr
    fmt = get_date_format_from_locale().replace("/", "")
    if fmt == "%d%m%Y":
        return "%d%m%Y"

    assert fmt == "%m%d%y"
    return "%m%d%Y"


CRISPY_FORMS_DATE_INPUT_FORMAT = get_crispy_forms_date_input_format()


def wait_until(fn: Callable[[], Any]) -> Any:
    """Retry an action until it succeeds or the maximum wait time is reached.

    Args:
        fn (Callable[[], Any]): The function to execute.

    Returns:
        Any: The result of the function call.

    Raises:
        ElementClickInterceptedException: If the action does not succeed within the
                                          allotted time.
    """
    start_time = time.time()
    while True:  # pylint: disable=while-used
        try:
            return fn()
        except ElementClickInterceptedException:  # pragma: no cover
            if time.time() - start_time > MAX_WAIT:
                raise
            time.sleep(0.1)


def _sign_into_website(browser: WebDriver, username: str) -> None:
    # He sees the Sign In button in the navbar
    sign_in_button = browser.find_element(By.LINK_TEXT, "Sign In")

    # He clicks on the Sign In button
    with suppress_fastdev_strict_if_deprecation_warning():
        sign_in_button.click()

    # This sends him to the Sign In page, where he notices that the page title and
    # the header mention Sign In
    assert "Sign In" in browser.title

    # He types "bob" into the Username field
    username_field = browser.find_element(By.ID, "id_login")
    username_field.send_keys(username)

    # He types "secret" into the Password field
    password_field = browser.find_element(By.ID, "id_password")
    password_field.send_keys(get_test_user_password())

    # He clicks the "Sign In" button
    sign_in_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    sign_in_button.click()

    # This takes him to his user page (where he can manage his user further).
    # He also sees this in the page title bar
    assert f"User: {username}" in browser.title, browser.title


def _sign_out_of_website_and_clean_up(browser: WebDriver) -> None:
    # He clicks on the Sign Out button
    sign_out_button = browser.find_element(By.LINK_TEXT, "Sign Out")

    with suppress_fastdev_strict_if_deprecation_warning():
        sign_out_button.click()

    # An "Are you sure you want to sign out?" dialog pops up, asking him to confirm
    # that he wants to sign out.
    confirm_sign_out_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    confirm_sign_out_button.click()

    # Also tidy up here by cleaning up all the browser cookies.
    browser.delete_all_cookies()

    # Satisfied, he goes back to sleep


def _check_maintenance_jobs_page_table_after_job_creation(browser: WebDriver) -> None:
    cell_texts = _check_maintenance_jobs_table(browser)["cell_texts"]

    ## Make sure the cell text contents match the expected values.
    assert cell_texts == [
        "1",  # Job Number
        "2021-01-01",  # Date (assigned by Agent)
        "Department of Home Affairs Bellville",
        "GPS",  # This is the displayed text, on-screen it's a link
        "Please fix the leaky faucet in the staff bathroom",
        "",  # Date of Inspection
        "",  # Quote
        "",  # Accept or Reject A/R
        "",  # Deposit POP
        "",  # Job Date
        "",  # Photos
        "",  # Invoice
        "",  # Comments
        "No",  # Job Complete
        "",  # Final Payment POP
    ], cell_texts


def _check_maintenance_jobs_page_table_after_job_completion(browser: WebDriver) -> None:
    row_info = _check_maintenance_jobs_table(browser)
    cell_texts = row_info["cell_texts"]

    ## Make sure the cell text contents match the expected values.
    expected = [
        "1",  # This is for the row number, automatically added by the system.
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",  # This is the displayed text, on-screen it's a link
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",  # Date of Inspection
        "Download Quote",  # Quote
        "A",  # Accept or Reject A/R
        "Download POP",  # Deposit POP
        "2021-03-02",  # Job Date
        "Download Photo 1 Download Photo 2",  # Job completion photos
        "Download Invoice",  # Invoice
        "I fixed the leaky faucet While I was in there I noticed damage in the wall "
        "Do you want me to fix that too?",
        "Yes",  # Job Complete
        "",  # Final Payment POP
    ]
    assert cell_texts == expected, f"Expected: {expected}, got: {cell_texts}"

    # Attempt to reach the browser using the browser.
    photo_urls = row_info["photo_urls"]

    # Get the current url of the browser:
    orig_url = browser.current_url

    for url in photo_urls:
        browser.get(url)

        # If the image is retrievable at the URL, then when we retrieve the page,
        # the browser in Chrome contains HTML to view the image in the browser.
        # We check for a short fragment of the expected HTML in that case.
        expected_html = f'src="{url}"'
        if expected_html not in browser.page_source:  # pragma: no cover
            msg = f"Failed to download photo from {url}"
            raise AssertionError(msg)

    # Browse back to our original URL:
    browser.get(orig_url)


def _check_maintenance_jobs_page_table_after_final_payment_pop_submission(
    browser: WebDriver,
) -> None:
    cell_texts = _check_maintenance_jobs_table(browser)["cell_texts"]

    ## Make sure the cell text contents match the expected values.
    expected = [
        "1",  # This is for the row number, automatically added by the system.
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",  # This is the displayed text, on-screen it's a link
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",  # Date of Inspection
        "Download Quote",  # Quote
        "A",  # Accept or Reject A/R
        "Download POP",  # Deposit POP
        "2021-03-02",  # Job Date
        "Download Photo 1 Download Photo 2",  # Job completion photos
        "Download Invoice",  # Invoice
        "I fixed the leaky faucet While I was in there I noticed damage in the wall "
        "Do you want me to fix that too?",  # Comments on the job
        "Yes",  # Job Complete
        "Download Final Payment POP",  # Final Payment POP
    ]
    assert cell_texts == expected, f"Expected: {expected}, got: {cell_texts}"


def _check_maintenance_jobs_table(browser: WebDriver) -> dict[str, list[str]]:
    """Check the maintenance jobs table for the correct row and cell contents.

    Args:
        browser (WebDriver): The Selenium WebDriver.

    Returns:
        list[str]: A list of cell texts from the table, containing job details.
    """
    # He notices that the new Maintenance Job is listed on the web page in a table
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be two rows:
    assert len(rows) == 2, len(rows)  # noqa: PLR2004

    ## The first row is the header row
    header_row = rows[0]
    header_cell_texts = [
        cell.text for cell in header_row.find_elements(By.TAG_NAME, "th")
    ]

    assert header_cell_texts == [
        "Number",
        "Date",
        "Address Details",
        "GPS Link",
        "Quote Request Details",
        "Date of Inspection",
        "Quote",
        "Accept or Reject A/R",
        "Deposit POP",
        "Job Date",
        "Photos",
        "Invoice",
        "Comments on the job",
        "Job Complete",
        "Final Payment POP",
    ], header_cell_texts

    ## The second row is the new job
    row = rows[1]

    # Prepare and return details extracted from the row
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]

    # Get the download URLs for the photo images
    photo_urls = []
    photo_cell = row.find_elements(By.TAG_NAME, "td")[10]
    photo_links = photo_cell.find_elements(By.TAG_NAME, "a")
    for link in photo_links:
        url = check_type(link.get_attribute("href"), str)
        assert url.endswith(".jpg")
        assert "/completion_photos/" in url
        photo_urls.append(url)

    return {
        "cell_texts": cell_texts,
        "photo_urls": photo_urls,
    }


def _create_new_job(
    browser: WebDriver,
    live_server_url: str,
) -> None:
    # pylint: disable=too-many-locals

    # Marnie's client Bob has heard of Marnie's cool new maintenance management site.
    # He goes to check out its homepage.
    browser.get(live_server_url)

    # He notices the page title
    assert "Marnie's Maintenance Manager" in browser.title

    ## Go through the process of logging into the website as 'bob' user:
    _sign_into_website(browser, "bob")

    # He sees some basic instructions on this page that tell him the next step that
    # he should click on the "Maintenance Jobs" link next.
    expected_msg = "Click on the 'Maintenance Jobs' link above to create a new job."
    assert expected_msg in browser.page_source

    # He sees the "Maintenance Jobs" link in the navbar
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")

    # He clicks on the "Maintenance Jobs" link
    maintenance_jobs_link.click()

    # This sends him to the "Maintenance Jobs" page, where he notices that the page
    # title and the header mention Jobs
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    # He notices a "Create Maintenance Job" link
    create_maintenance_job_link = browser.find_element(
        By.LINK_TEXT,
        "Create Maintenance Job",
    )

    # He clicks on the "Create Maintenance Job" link
    create_maintenance_job_link.click()

    # This sends him to the "Create Maintenance Job" page, where he notices that
    # the page title and the header mention Create Maintenance Job
    assert "Create Maintenance Job" in browser.title
    assert "Create Maintenance Job" in browser.find_element(By.TAG_NAME, "h1").text

    # He notices entry fields "Date", "Address Details", "GPS Link", and "Quote
    # Request Details", as well as a "Submit" button
    date_field = browser.find_element(By.ID, "id_date")
    address_details_field = browser.find_element(By.ID, "id_address_details")
    gps_link_field = browser.find_element(By.ID, "id_gps_link")
    quote_request_details_field = browser.find_element(
        By.ID,
        "id_quote_request_details",
    )
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He types 01/01/2021 into the "Date" field (dd/mm/yyyy) format.
    # It's a custom input field that adds the "-" values in for us.
    date_field.send_keys("01012021")

    # He types "Department of Home Affairs Bellville" into the "Address Details"
    # field
    address_details_field.send_keys("Department of Home Affairs Bellville")

    # He copy-pastes "https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7" into the
    # "GPS Link" field
    gps_link_field.send_keys("https://maps.app.goo.gl/mXfDGVfn1dhZDxJj7")

    # He types "Please fix the leaky faucet in the staff bathroom" into the
    # "Quote Request Details" field
    quote_request_details_field.send_keys(
        "Please fix the leaky faucet in the staff bathroom",
    )

    # Scroll the page down to bring the Submit button into view if it is not already:
    browser.execute_script(  # type: ignore[no-untyped-call]
        "window.scrollTo(0, document.body.scrollHeight);",
    )

    # He clicks the Submit button
    wait_until(submit_button.click)

    # This sends him back to the "Maintenance Jobs" page, where he notices that the
    # page title and the header mention Maintenance Jobs like before.
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    ## Thoroughly check that the table has the correct headings and row contents.
    _check_maintenance_jobs_page_table_after_job_creation(browser)

    # Satisfied, he goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


def _check_job_row_and_click_on_number(browser: WebDriver) -> None:
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be exactly one row here
    assert len(rows) == 2  # noqa: PLR2004

    ## Get the row, and confirm that the details include everything submitted up until
    ## now.
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
    assert cell_texts == [
        "1",
        "2021-01-01",
        "Department of Home Affairs Bellville",
        "GPS",
        "Please fix the leaky faucet in the staff bathroom",
        "2021-02-01",
        "Download Quote",
        "",  # Accept or Reject A/R
        "",  # Deposit POP
        "",  # Job Date
        "",  # Photos
        "",  # Invoice
        "",  # Comments
        "No",  # Job Complete
        "",  # Final Payment POP
    ], cell_texts

    # He clicks on the #1 number again:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()


def _marnie_logs_in_and_navigates_to_bob_jobs(browser: WebDriver) -> None:
    """Simulate Marnie to logging in and navigating to Bob's jobs page.

    Args:
        browser (WebDriver): The Selenium WebDriver.
    """
    # Marnie logs in
    _sign_into_website(browser, "marnie")

    # Then he looks for the "Agents" link and clicks on it:
    agents_link = browser.find_element(By.LINK_TEXT, "Agents")
    agents_link.click()

    # He sees a list of agents, and clicks on Bob's username:
    bob_link = browser.find_element(By.LINK_TEXT, "bob")
    bob_link.click()


def _sign_in_as_marnie_and_navigate_to_job_details(browser: WebDriver) -> None:
    # Marnie logs in, and navigates to Bob's jobs page
    _marnie_logs_in_and_navigates_to_bob_jobs(browser)

    # This takes him to the Maintenance Jobs page for Bob the Agent.

    # He clicks on the link with the number 1 in the text:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()


def _update_job_with_inspection_date_and_quote(browser: WebDriver) -> dict[str, str]:
    # Marnie logs into the system and navigates through to the detail page of the job
    _sign_in_as_marnie_and_navigate_to_job_details(browser)

    # Just below the existing details, he sees a "Complete Inspection" link.
    update_link = browser.find_element(By.LINK_TEXT, "Complete Inspection")

    # He clicks on the Edit link
    update_link.click()

    # On the next page, he sees that the page title and header mention "Update
    # Maintenance Job"
    assert "Complete Inspection" in browser.title, browser.title
    assert "Complete Inspection" in browser.find_element(By.TAG_NAME, "h1").text

    # He also sees on this page, that he can edit (only) these fields:
    # - Date of Inspection
    inspection_date_field = browser.find_element(By.ID, "id_date_of_inspection")

    # - Quote (an invoice to be uploaded by Marnie, for the fixes to be done for
    #   the site he has visited)>
    quote_invoice_field = browser.find_element(By.ID, "id_quote")

    # As well as a "submit" button just below those two:
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # But in particular, he doesn't see fields that only the Agent should be able to
    # edit, while submitting the job.
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_date")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_address_details")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_gps_link")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "id_quote_request_details")

    # He inputs a date into the inspection date field.
    input_date = datetime.date(2021, 2, 1)
    keys = input_date.strftime(CRISPY_FORMS_DATE_INPUT_FORMAT)
    inspection_date_field.send_keys(keys)

    # He uploads a Quote invoice.
    quote_invoice_field.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test.pdf"))

    # He clicks the "submit" button.
    submit_button.click()

    # This takes him back to the Maintenance Jobs page for Bob the Agent.
    assert "Maintenance Jobs for bob" in browser.title
    assert "Maintenance Jobs for bob" in browser.find_element(By.TAG_NAME, "h1").text

    # He also sees a flash notification that an email has been sent to Bob.
    expected_msg = "An email has been sent to bob."
    assert expected_msg in browser.page_source

    # He sees that the new details are now listed in the table.
    _check_job_row_and_click_on_number(browser)

    # Over here he can now see the inspection date:
    assert "2021-02-01" in browser.page_source

    # And also, there is a link to the Quote invoice, with the text "Download Quote":
    quote_link = browser.find_element(By.LINK_TEXT, "Download Quote")

    # If he looks at the link more closely, he can see it's a PDF file:
    download_url = quote_link.get_attribute("href")
    assert isinstance(download_url, str)

    ## Example href values:
    ## - 'http://django:41507/protected_media/quotes/test.pdf'
    ## - 'https://mmm-staging2.ar-ciel.org/protected_media/quotes/test_oMjXoTi.pdf'
    ## - 'http://django:47053/private-media/quotes/test_4labiyd.pdf'
    assert "/private-media/quotes/test" in download_url
    assert download_url.endswith(".pdf")

    ## Sign out and tidy up cookies:
    _sign_out_of_website_and_clean_up(browser)

    # Return quote_download url to the caller:
    return {
        "quote_download_url": download_url,
    }


def _bob_rejects_marnies_quote(browser: WebDriver) -> None:
    """Ensure Bob can reject the quote submitted by Marnie.

    Args:
        browser (WebDriver): The Selenium WebDriver.
    """
    # Bob receives the email notification that Marnie has done the initial inspection,
    # so he signs in to the website
    _sign_into_website(browser, "bob")

    # He clicks on the "Maintenance Jobs" link:
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # He can see from the Title and the Heading that he is in the "Maintenance Jobs"
    # page.
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees his original job details over there.
    _check_job_row_and_click_on_number(browser)

    # He can see from the Title and the Heading that he is in the "Maintenance Job
    # Details" page.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a "Reject Quote" button and an "Accept Quote" button.
    reject_button = browser.find_element(By.XPATH, "//button[text()='Reject Quote']")
    browser.find_element(By.XPATH, "//button[text()='Accept Quote']")

    # He clicks on the "Reject Quote" button.
    reject_button.click()

    # A message flash comes up, saying that Marnie was emailed
    expected_msg = "Quote rejected. An email has been sent to Marnie."
    assert expected_msg in browser.page_source

    # He now sees a "Job Status: Rejected" entry on the page.
    assert "<strong>Accepted or Rejected (A/R):</strong> R" in browser.page_source

    # He does not see the "Rejected Job" button any longer.
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.LINK_TEXT, "Reject Quote")

    # He does still see an "Accept Job" button.
    accept_button = browser.find_element(By.XPATH, "//button[text()='Accept Quote']")
    assert accept_button is not None

    # He clicks on the "Maintenance Jobs" link to take him back to the main listing
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # In the "Accept or Reject A/R" cell of his Job in the listing, he can see the
    # text "Rejected"
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")
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
        "R",  # Accept or Reject A/R
        "",  # Deposit POP
        "",  # Job Date
        "",  # Job Completion Photos
        "",  # Invoice
        "",  # Comments
        "No",  # Job Complete
        "",  # Final Payment POP
    ]
    assert cell_texts == expected, f"Expected: {expected}, got: {cell_texts}"

    # Satisfied, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


def _bob_accepts_marnies_quote(browser: WebDriver) -> None:
    # Bob received a notification. He saw the email, and the quote, and is happy with
    # it, so he is ready to confirm the quote. He logs into the system:
    _sign_into_website(browser, "bob")

    # Then he goes to the Maintenance Jobs page:
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # He sees the details of the job, and clicks on the number to view the details:
    _check_job_row_and_click_on_number(browser)

    # He sees the details of the job, and clicks on the "Accept Quote" button:
    accept_button = browser.find_element(By.XPATH, "//button[text()='Accept Quote']")
    accept_button.click()

    # This takes him back to the details page for the Job.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a flash notification that an email has been sent to Marnie.
    expected_msg = "An email has been sent to Marnie."
    assert expected_msg in browser.page_source

    # He sees an "Accepted or Rejected (A/R): A" entry on the page.
    assert "<strong>Accepted or Rejected (A/R):</strong> A" in browser.page_source

    # He does not see the "Accept Quote" button any longer.
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.LINK_TEXT, "Accept Quote")

    # He does not see the "Reject Quote" button any longer.
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.LINK_TEXT, "Reject Quote")

    # Unlike other reused functions, we don't leave the browser here. That's because
    # Bob, in other tests, continues doing other actions before he's done and its
    # Marnies turn to do something.


def _bob_submits_deposit_pop(browser: WebDriver) -> None:
    ## At this point, Bob should still be logged into the system, and the current page
    ## should be the "Maintenance Job Details" page. Confirm that:
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees an "Upload Deposit POP" link, and clicks on it.
    submit_pop_link = browser.find_element(
        By.LINK_TEXT,
        "Upload Deposit POP",
    )
    submit_pop_link.click()

    # He sees the "Upload Deposit POP" page, with the title and header mentioning the
    # same.
    assert "Upload Deposit POP" in browser.title
    assert "Upload Deposit POP" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees the "Proof of Payment" field, and a "Submit" button.
    pop_field = browser.find_element(By.ID, "id_deposit_proof_of_payment")
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He uploads a Proof of Payment.
    pop_field.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test.pdf"))

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

    # Over in the job details page he can see the link to his previously uploaded file,
    # with the text "Download Deposit POP":
    pop_link_elem = browser.find_element(By.LINK_TEXT, "Download Deposit POP")
    assert pop_link_elem is not None


def _marnie_completes_the_job(browser: WebDriver) -> None:
    # Bob logs out
    _sign_out_of_website_and_clean_up(browser)

    # Marnie logs in and goes to the job details.
    _sign_in_as_marnie_and_navigate_to_job_details(browser)

    # He can see a "Complete Job" link at the bottom of the page.
    update_link = browser.find_element(By.PARTIAL_LINK_TEXT, "Complete Job")

    # He clicks on the "Complete Job" link.
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
    input_date = datetime.date(2021, 3, 2)
    keys = input_date.strftime(CRISPY_FORMS_DATE_INPUT_FORMAT)
    job_date_input.send_keys(keys)

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
    invoice_input.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test.pdf"))

    # He sees an "Add photo" button, and clicks on it.
    add_photo_button = browser.find_element(By.ID, "add-photo")
    add_photo_button.click()

    # He sees a field where he can upload a photo for the work done:
    photo_input = browser.find_element(By.NAME, "form-0-photo")

    # He uploads a photo file:
    photo_input.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test.jpg"))

    # He adds a second photo.
    add_photo_button.click()
    photo_input = browser.find_element(By.NAME, "form-1-photo")
    photo_input.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test_2.jpg"))

    # He sees a "Submit" button and clicks it:
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    submit_button.click()

    # He is taken back to the maintenance jobs page for Bob.
    assert browser.title == "Maintenance Jobs for bob", browser.title
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
    href = check_type(invoice_link.get_attribute("href"), str)

    # Example href value:
    #   'http://django:36549/private-media/invoices/test_iaW5hcE.pdf'
    assert "/private-media/invoices/test" in href
    assert href.endswith(".pdf")

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

    # He sees links to the photos that he uploaded earlier:
    link_texts = ["Download Photo 1", "Download Photo 2"]
    for link_text in link_texts:
        photo_link = browser.find_element(By.LINK_TEXT, link_text)
        assert photo_link is not None
        assert link_text in photo_link.text
        url = check_type(photo_link.get_attribute("href"), str)
        assert url.endswith(".jpg")

    # Happy with this, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


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
    _marnie_completes_the_job(browser)
