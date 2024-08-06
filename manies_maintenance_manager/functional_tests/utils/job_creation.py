"""Utility functions for creating and managing jobs in functional tests.

This module contains functions that simulate the process of creating new jobs,
updating job details, and performing various actions related to job management
such as accepting quotes and submitting proofs of payment.
"""

# pylint: disable=magic-value-comparison,disable=too-many-statements,too-many-locals
# ruff: noqa: ERA001, PLR0915

import datetime

import pytest
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from typeguard import check_type

from .common import wait_until
from .constants import FUNCTIONAL_TESTS_DATA_DIR
from .date_utils import CRISPY_FORMS_DATE_INPUT_FORMAT
from .login import _sign_into_website
from .login import _sign_out_of_website_and_clean_up
from .page_checks import _check_job_row_and_click_on_number
from .page_checks import (
    _check_maintenance_jobs_page_after_manie_uploaded_his_final_docs,
)
from .page_checks import _check_maintenance_jobs_page_table_after_job_creation


def _create_new_job(browser: WebDriver, live_server_url: str) -> None:
    # Manie's client Bob has heard of Manie's cool new maintenance management site.
    # He goes to check out its homepage.
    browser.get(live_server_url)

    # He notices the page title
    assert "Manie's Maintenance Manager" in browser.title

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
    assert "Maintenance Jobs" in browser.title, browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    ## Thoroughly check that the table has the correct headings and row contents.
    _check_maintenance_jobs_page_table_after_job_creation(browser)

    # Satisfied, he goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


def _update_job_with_inspection_date_and_quote(browser: WebDriver) -> dict[str, str]:
    # Manie logs into the system and navigates through to the detail page of the job
    _sign_into_website(browser, "manie")

    # Then he looks for the "Agents" link and clicks on it:
    agents_link = browser.find_element(By.LINK_TEXT, "Agents")
    agents_link.click()

    # He sees a list of agents, and clicks on Bob's username:
    bob_link = browser.find_element(By.LINK_TEXT, "bob")
    bob_link.click()

    # He clicks on the link with the number 1 in the text:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()

    # Just below the existing details, he sees a "Complete Inspection" link.
    update_link = browser.find_element(By.LINK_TEXT, "Complete Inspection")

    # He clicks on the Edit link
    update_link.click()

    # On the next page, he sees that the page title and header mention "Update
    # Maintenance Job"
    assert "Complete Inspection" in browser.title, browser.title
    assert "Complete Inspection" in browser.find_element(By.TAG_NAME, "h1").text

    # He also sees on this page, the only editable field is the "Date of Inspection"
    inspection_date_field = browser.find_element(By.ID, "id_date_of_inspection")

    # There is a "submit" button just below the field:
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He inputs a date into the inspection date field.
    # In his workflow, this is typically while he is on his way out, from the original
    # site inspection.
    input_date = datetime.date(2021, 2, 1)
    keys = input_date.strftime(CRISPY_FORMS_DATE_INPUT_FORMAT)
    inspection_date_field.send_keys(keys)

    # He clicks the "submit" button.
    submit_button.click()

    # This takes him back to the Maintenance Jobs page for Bob the Agent.
    assert "Maintenance Jobs for bob" in browser.title, browser.title
    assert "Maintenance Jobs for bob" in browser.find_element(By.TAG_NAME, "h1").text

    # He also sees a flash notification that an email has been sent to Bob.
    expected_msg = "An email has been sent to bob."
    assert expected_msg in browser.page_source

    # He sees that the new details are now listed in the table, and then click son the
    # "1" link. At the same time, he should not see a quote download link.
    _check_job_row_and_click_on_number(browser, quote_expected=False)

    # After that, Manie should be back on the Job Details page.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # Over here he can now see the inspection date:
    assert "2021-02-01" in browser.page_source

    # Let's assume that Manie has done the work at home necessary to generate the
    # invoice PDF file, and he is now ready to upload it to the system under the
    # job where he already input the inspection date.

    # He sees a "Upload Quote" link, and clicks on it.
    submit_quote_link = browser.find_element(By.LINK_TEXT, "Upload Quote")
    submit_quote_link.click()

    # He sees the "Upload Quote" page, with the title and header mentioning the same.
    assert "Upload Quote" in browser.title
    assert "Upload Quote" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees the "Quote" field, and a "Submit" button.
    quote_invoice_field = browser.find_element(By.ID, "id_quote")
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He uploads a Quote.
    quote_invoice_field.send_keys(str(FUNCTIONAL_TESTS_DATA_DIR / "test.pdf"))

    # He clicks the "submit" button.
    submit_button.click()

    # This takes him back to the Job-listing page.
    assert "Maintenance Jobs for bob" in browser.title, browser.title
    assert "Maintenance Jobs for bob" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a flash notification that an email has been sent to Bob.
    expected_msg = "An email has been sent to bob."
    assert expected_msg in browser.page_source

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


def _bob_accepts_manies_quote(browser: WebDriver) -> None:
    # Bob received a notification. He saw the email, and the quote, and is happy with
    # it, so he is ready to confirm the quote. He logs into the system:
    _sign_into_website(browser, "bob")

    # Then he goes to the Maintenance Jobs page:
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # He sees the details of the job, and clicks on the number to view the details:
    _check_job_row_and_click_on_number(browser, quote_expected=True)

    # He sees the details of the job, and clicks on the "Accept Quote" button:
    accept_button = browser.find_element(By.XPATH, "//button[text()='Accept Quote']")
    accept_button.click()

    # This takes him back to the details page for the Job.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a flash notification that an email has been sent to Manie.
    expected_msg = "An email has been sent to Manie."
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
    # Manies turn to do something.


def _bob_rejects_manies_quote(browser: WebDriver) -> None:
    """Ensure Bob can reject the quote submitted by Manie.

    Args:
        browser (WebDriver): The Selenium WebDriver.
    """
    # Bob receives the email notification that Manie has done the initial inspection,
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
    _check_job_row_and_click_on_number(browser, quote_expected=True)

    # He can see from the Title and the Heading that he is in the "Maintenance Job
    # Details" page.
    assert "Maintenance Job Details" in browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a "Reject Quote" button and an "Accept Quote" button.
    reject_button = browser.find_element(By.XPATH, "//button[text()='Reject Quote']")
    browser.find_element(By.XPATH, "//button[text()='Accept Quote']")

    # He clicks on the "Reject Quote" button.
    reject_button.click()

    # A message flash comes up, saying that Manie was emailed
    expected_msg = "Quote rejected. An email has been sent to Manie."
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
        "",  # Final Payment POP
        "No",  # Job Complete
    ]
    assert cell_texts == expected, f"Expected: {expected}, got: {cell_texts}"

    # Satisfied, he logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)


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

    # He sees a flash notification that an email has been sent to Manie.
    expected_msg = (
        "Your Deposit Proof of Payment has been uploaded. An email has "
        "been sent to Manie."
    )
    assert expected_msg in browser.page_source

    # Over in the job details page he can see the link to his previously uploaded file,
    # with the text "Download Deposit POP":
    pop_link_elem = browser.find_element(By.LINK_TEXT, "Download Deposit POP")
    assert pop_link_elem is not None


def _manie_does_onsite_work_then_uploads_his_final_docs(
    browser: WebDriver,
) -> None:
    # Bob logs out
    _sign_out_of_website_and_clean_up(browser)

    # Manie logs in and goes to the job details.
    from manies_maintenance_manager.functional_tests.utils.navigation import (  # pylint: disable=import-outside-toplevel
        _sign_in_as_manie_and_navigate_to_job_details,
    )

    _sign_in_as_manie_and_navigate_to_job_details(browser)

    # He can see a "Record Job Date" link at the bottom of the page.
    record_job_onsite_work_completion_date_link = browser.find_element(
        By.PARTIAL_LINK_TEXT,
        "Record Onsite Work Completion",
    )

    # He clicks on the "Record Job Date" link.
    record_job_onsite_work_completion_date_link.click()

    # He is taken to a "Record Job Date" page. He can see that title both
    # in the browser tab and on the page itself as its heading.
    assert "Record Onsite Work Completion" in browser.title, browser.title
    heading = browser.find_element(By.TAG_NAME, "h1")
    assert "Record Onsite Work Completion" in heading.text, heading.text

    # He sees a field where he can input the Job (physical completion) Date:
    job_onsite_work_completion_date_input = browser.find_element(
        By.NAME,
        "job_onsite_work_completion_date",
    )
    assert job_onsite_work_completion_date_input is not None

    # He enters the job (physical completion) date:
    input_date = datetime.date(2021, 3, 2)
    keys = input_date.strftime(CRISPY_FORMS_DATE_INPUT_FORMAT)
    job_onsite_work_completion_date_input.send_keys(keys)

    # On the current page, none of these inputs should be present:
    # - comments, invoices, or photos
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.NAME, "comments")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.NAME, "invoice")
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.ID, "add-photo")

    # He sees a "Submit" button and clicks it:
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")
    submit_button.click()

    # He is taken back to the maintenance jobs page for Bob.
    assert browser.title == "Maintenance Jobs for bob", browser.title
    assert browser.find_element(By.TAG_NAME, "h1").text == "Maintenance Jobs for bob"

    # He sees a flash notification that the job has been completed.
    expected_msg = (
        "Onsite work has been flagged as completed. An email has been sent to bob."
    )
    assert expected_msg in browser.page_source

    # Click on #1 again, and this should take us to the job details again:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()
    assert "Maintenance Job Details" in browser.title, browser.title
    assert "Maintenance Job Details" in browser.find_element(By.TAG_NAME, "h1").text

    # Click on the "Submit Job Documentation" button:
    submit_documentation_link = browser.find_element(
        By.PARTIAL_LINK_TEXT,
        "Submit Job Documentation",
    )
    submit_documentation_link.click()

    # He sees the "Submit Job Documentation" page, with the title and header mentioning
    # the same.
    assert "Submit Job Documentation" in browser.title
    assert "Submit Job Documentation" in browser.find_element(By.TAG_NAME, "h1").text

    # There shouldn't be a "Job Date" field on this page:
    with pytest.raises(NoSuchElementException):
        browser.find_element(By.NAME, "job_onsite_work_completion_date")

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
    expected_msg = "Documentation has been submitted. An email has been sent to bob."
    assert expected_msg in browser.page_source

    # He checks the job-listing page in detail, that his there and in the expected
    # state.
    _check_maintenance_jobs_page_after_manie_uploaded_his_final_docs(browser)

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
    job_onsite_work_completion_date = browser.find_element(By.CLASS_NAME, "job-date")
    assert job_onsite_work_completion_date is not None
    assert "2021-03-02" in job_onsite_work_completion_date.text

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
