"""Tests for the agent exporting jobs to a spreadsheet."""

import csv
from io import StringIO
from pathlib import Path

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.functional_tests.utils.login import _sign_into_website
from marnies_maintenance_manager.functional_tests.utils.workflows import (
    _workflow_from_new_job_to_final_pop_added_by_bob,
)
from marnies_maintenance_manager.users.models import User

FUNCTIONAL_TESTS_DATA_DIR = Path(__file__).resolve().parent


def test_agent_exports_jobs_to_spreadsheet(
    browser: WebDriver,
    live_server_url: str,
    marnie_user: User,  # pylint: disable=unused-argument
    bob_agent_user: User,  # pylint: disable=unused-argument
) -> None:
    """Test that Bob can export the jobs to a spreadsheet.

    Args:
        browser (WebDriver): The Selenium WebDriver.
        live_server_url (str): The URL of the live server.
        marnie_user (User): The user instance for Marnie.
        bob_agent_user (User): The user instance for Bob, who is an agent.
    """
    # Perform the complete workflow to get from no jobs, to a completed job, which
    # also includes the final payment proof of payment.
    _workflow_from_new_job_to_final_pop_added_by_bob(browser, live_server_url)

    # Log in again as bob, and then navigate over to his job-listing page:
    _sign_into_website(browser, "bob")
    maintenance_jobs_link = browser.find_element(By.LINK_TEXT, "Maintenance Jobs")
    maintenance_jobs_link.click()

    # Bob sees the list of jobs, as well as a button to "Export to Spreadsheet"
    export_to_spreadsheet_button = browser.find_element(
        By.ID,
        "export-to-spreadsheet-button",
    )

    ## We want to add "?display=inline" to the URL so that the browser will display the
    ## contents inline rather than triggering a download.
    export_to_spreadsheet_button_url = export_to_spreadsheet_button.get_attribute(
        "href",
    )
    assert isinstance(export_to_spreadsheet_button_url, str)
    export_to_spreadsheet_button_url += "?display=inline"
    browser.get(export_to_spreadsheet_button_url)

    # Get the source for the current page:
    source = browser.page_source

    # Use beautiful soup to extract the text contents (not the BeautifulSoup object)
    # of the "pre" tag from the source:
    soup = BeautifulSoup(source, "html.parser")
    pre_tag = soup.find("pre")
    assert pre_tag is not None
    pre_tag_text = pre_tag.get_text()

    # Parse that as CSV data, and retrieve a list of dictionaries:
    csv_file = StringIO(pre_tag_text)
    csv_reader = csv.DictReader(csv_file)
    jobs = list(csv_reader)

    # Confirm that the retrieved contents are as expected:
    # fmt: off
    assert jobs == [
        {
            "Accept or Reject A/R": "A",
            "Address Details": "Department of Home Affairs Bellville",
            "Comments on the job": "I fixed the leaky faucet\n"
            "While I was in there I noticed damage in the wall\n"
            "Do you want me to fix that too?",
            "Date": "2021-01-01",
            "Date of Inspection": "2021-02-01",
            "Job Complete": "Yes",
            "Job Date": "2021-03-02",
            "Number": "1",
            "Quote Request Details":
                "Please fix the leaky faucet in the staff bathroom",
        },
    ]
    # fmt: on
