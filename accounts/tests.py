# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from accounts.models import UnoUser
from datetime import datetime
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver

import os


class UnoUserTestCase(TestCase):

    def test_user_creation(self):
        josh = UnoUser.objects.create(
            first_name="Josh",
            last_name="Sunshiine",
            username="jsun",
            password="password",
            gender="MALE",
            date_of_birth=datetime.now(),
        )
        self.assertIsNotNone(josh)


class SeleniumTests(StaticLiveServerTestCase):
    timeout = 10

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        if os.environ.get('USER') == 'tonypoe':
            chrome_driver = os.getcwd() + os.sep + 'chromedriver_mac'
        else:
            chrome_driver = os.getcwd() + os.sep + 'chromedriver'
        cls.selenium = WebDriver(chrome_driver, options=chrome_options)
        cls.selenium.implicitly_wait(SeleniumTests.timeout)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_selenium_account_creation(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.selenium.find_element_by_id('id_first_name').send_keys('Michael')
        self.selenium.find_element_by_id('id_last_name').send_keys('Hilton')
        self.selenium.find_element_by_id(
            'id_email').send_keys('mhilton@hilton.com')
        # Ignore the first one as it relates to the login section instead
        self.selenium.find_elements_by_name('username')[1].send_keys('mhilton')
        self.selenium.find_element_by_id('id_password1').send_keys("password")
        self.selenium.find_element_by_id('id_password2').send_keys("password")
        self.selenium.find_element_by_id('register-btn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        mike = UnoUser.objects.filter(username='mhilton').first()

        self.assertIsNotNone(mike)
