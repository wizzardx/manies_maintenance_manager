"""Test user story: Agent uploads final payment proof of payment."""

# pylint: disable=magic-value-comparison,unused-argument,disable=too-many-locals

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils import (
    _check_maintenance_jobs_page_table_after_final_pop_submission,
)
from marnies_maintenance_manager.functional_tests.utils import _sign_into_website
from marnies_maintenance_manager.functional_tests.utils import (
    _sign_out_of_website_and_clean_up,
)
from marnies_maintenance_manager.functional_tests.utils import (
    _workflow_from_new_job_to_completed_by_marnie,
)
from marnies_maintenance_manager.users.models import User


def test_agent_uploads_final_payment_pop(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Test that Bob can upload the final payment proof of payment.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
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
        "Download Invoice",  # Invoice
        "I fixed the leaky faucet While I was in there I noticed damage in the "
        "wall Do you want me to fix that too?",  # Comments
        "Yes",  # Job Complete
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

    # He sees a form with a file input field, and a submit button.
    file_input = browser.find_element(By.ID, "id_proof_of_payment")
    submit_button = browser.find_element(By.CLASS_NAME, "btn-primary")

    # He uploads the final payment proof of payment.
    file_input.send_keys("/path/to/final_payment_pop.pdf")

    # He clicks the submit button.
    submit_button.click()

    # This takes him back to the job listing page.
    assert "Maintenance Jobs" in browser.title
    assert "Maintenance Jobs" in browser.find_element(By.TAG_NAME, "h1").text

    # He sees a popup message informing him that the final payment proof of payment
    # has been submitted successfully, and that Marnie has been emailed.

    # He sees the table with the job details, and the final payment proof of payment
    # link in the table.
    _check_maintenance_jobs_page_table_after_final_pop_submission(browser)

    # He also wants to check the job details page, so he clicks on the job number link.
    job_number_link = browser.find_element(By.LINK_TEXT, "1")
    job_number_link.click()

    # He sees the job details page, with the final payment proof of payment link.
    final_pop_link = browser.find_element(
        By.LINK_TEXT,
        "Download Final Payment Proof of Payment",
    )
    assert final_pop_link is not None

    # He logs out of the website, and goes back to sleep
    _sign_out_of_website_and_clean_up(browser)

    pytest.fail("Complete the test!")
