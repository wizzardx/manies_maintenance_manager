from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class CustomStaticLiveServerTestCase(StaticLiveServerTestCase):
    # Bind to all interfaces. This is so that in our dev environment, Chrome
    # running under Selenium in another Docker container, can connect to
    # our container. This is a bit of an ugly workaround to the default
    # `StaticLiveServerTestCase` behavior.
    host = "0.0.0.0"  # noqa: S104

    @property
    def live_server_url(self):
        """
        Returns the live server URL with the internal Docker service name.
        """
        return f"http://django:{self.server_thread.port}"


class MySeleniumTests(CustomStaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        # You can add more options here if needed
        cls.browser = webdriver.Remote(
            command_executor="http://chrome:4444/wd/hub",
            options=options,
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def test_example(self):
        self.browser.get(f"{self.live_server_url}/some_page")
        # Add assertions or interactions here
