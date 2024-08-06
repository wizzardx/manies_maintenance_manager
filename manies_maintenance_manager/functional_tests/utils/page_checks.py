"""Utility functions for verifying page contents in functional tests.

This module provides functions to check the contents of various pages,
particularly the maintenance jobs table, ensuring that the correct information
is displayed after different actions have been performed.
"""

# pylint: disable=magic-value-comparison,consider-using-assignment-expr

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from typeguard import check_type

from manies_maintenance_manager.jobs.constants import JOB_LIST_TABLE_COLUMN_NAMES


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
        "",  # Final Payment POP
        "No",  # Job Complete
    ], cell_texts


def _check_maintenance_jobs_page_after_manie_uploaded_his_final_docs(
    browser: WebDriver,
) -> None:
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
        "",  # Final Payment POP
        "No",  # Job Complete
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
        "Download Final Payment POP",  # Final Payment POP
        "Yes",  # Job Complete
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

    assert header_cell_texts == JOB_LIST_TABLE_COLUMN_NAMES, header_cell_texts

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


def _check_job_row_and_click_on_number(
    browser: WebDriver,
    *,
    quote_expected: bool,
) -> None:
    table = browser.find_element(By.ID, "id_list_table")
    rows = table.find_elements(By.TAG_NAME, "tr")

    ## There should be exactly one row here
    assert len(rows) == 2  # noqa: PLR2004

    ## Get the row, and confirm that the details include everything submitted up until
    ## now.
    row = rows[1]
    cell_texts = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]

    expected_cell_texts = [
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
        "",  # Final Payment POP
        "No",  # Job Complete
    ]

    # If there shouldn't be a quote, then update the expected cell texts.
    if not quote_expected:
        download_quote_idx = 6
        assert expected_cell_texts[download_quote_idx] == "Download Quote"
        expected_cell_texts[download_quote_idx] = ""

    # Now check:
    assert cell_texts == expected_cell_texts

    # He clicks on the #1 number again:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()
