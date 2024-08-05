"""Utility functions for handling login and logout operations in functional tests.

This module provides functions to simulate user login and logout actions,
including handling of browser cookies and session management.
"""

# pylint: disable=magic-value-comparison

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from marnies_maintenance_manager.jobs.tests.utils import (
    suppress_fastdev_strict_if_deprecation_warning,
)
from marnies_maintenance_manager.jobs.utils import get_test_user_password


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
