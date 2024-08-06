"""Utility functions for navigating through the application in functional tests.

This module provides functions to simulate user navigation through various
pages of the application, particularly focusing on Manie's interactions
with Bob's jobs.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .login import _sign_into_website


def _manie_logs_in_and_navigates_to_bob_jobs(browser: WebDriver) -> None:
    """Simulate Manie to logging in and navigating to Bob's "jobs" page.

    Args:
        browser (WebDriver): The Selenium WebDriver.
    """
    # Manie logs in
    _sign_into_website(browser, "manie")

    # Then he looks for the "Agents" link and clicks on it:
    agents_link = browser.find_element(By.LINK_TEXT, "Agents")
    agents_link.click()

    # He sees a list of agents, and clicks on Bob's username:
    bob_link = browser.find_element(By.LINK_TEXT, "bob")
    bob_link.click()


def _sign_in_as_manie_and_navigate_to_job_details(browser: WebDriver) -> None:
    # Manie logs in, and navigates to Bob's jobs page
    _manie_logs_in_and_navigates_to_bob_jobs(browser)

    # This takes him to the Maintenance Jobs page for Bob the Agent.

    # He clicks on the link with the number 1 in the text:
    number_link = browser.find_element(By.LINK_TEXT, "1")
    number_link.click()
