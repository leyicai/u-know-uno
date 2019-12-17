# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from accounts.models import UnoUser
from datetime import datetime
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, TestCase
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from unoGame.models import Game, GameRecord, Player

import os


class GameTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.aux_client = Client()
        super(GameTestCase, self).setUp()

    def create_josh_sunshine(self):
        josh = UnoUser.objects.create(
            first_name="Josh",
            last_name="Sunshiine",
            username="jsun",
            password="password",
            email="josh@sunshine.com",
            gender="MALE",
            date_of_birth=datetime.now(),
        )
        josh.set_password('password')
        josh.save()
        return josh

    def create_michael_hilton(self):
        mike = UnoUser.objects.create(
            first_name="Michael",
            last_name="Hilton",
            username="mhilton",
            email="mhilton@mike.com",
            password="password",
            gender="MALE",
            date_of_birth=datetime.now(),
        )
        mike.set_password('password')
        mike.save()
        return mike

    def test_game_creation(self):
        josh = self.create_josh_sunshine()

        self.client.force_login(josh)
        self.client.get('/game/create/')
        created_game = Game.objects.get_or_none(id=1)

        self.assertIsNotNone(created_game)

    def test_game_password_creation(self):
        josh = self.create_josh_sunshine()

        self.client.force_login(josh)
        self.client.get('/game/create/')
        self.client.get('/game/1/generatePassword/')
        created_game = Game.objects.get_or_none(id=1)

        self.assertIsNotNone(created_game)
        self.assertIsNotNone(created_game.password)


class SeleniumTests(StaticLiveServerTestCase):
    timeout = 10

    def create_michael_hilton(self):
        mike = UnoUser.objects.create(
            first_name="Michael",
            last_name="Hilton",
            username="mhilton",
            email="mhilton@mike.com",
            password="password",
            gender="MALE",
            date_of_birth=datetime.now(),
        )
        mike.set_password('password')
        mike.save()
        return mike

    def create_josh_sunshine(self):
        josh = UnoUser.objects.create(
            first_name="Josh",
            last_name="Sunshiine",
            username="jsun",
            password="password",
            email="josh@sunshine.com",
            gender="MALE",
            date_of_birth=datetime.now(),
        )
        josh.set_password('password')
        josh.save()
        return josh

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

    def test_selenium_game_creation(self):
        mike = self.create_michael_hilton()
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.selenium.find_element_by_id(
            'id_username').send_keys(mike.username)
        self.selenium.find_element_by_id('id_password').send_keys("password")
        self.selenium.find_element_by_id('login-btn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        self.selenium.get('%s%s' % (self.live_server_url, '/game/create/'))
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        created_game = Game.objects.all().first()
        self.assertIsNotNone(created_game)

    def test_selenium_create_game_with_password(self):
        josh = self.create_josh_sunshine()

        # Create game with password
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.selenium.find_element_by_id(
            'id_username').send_keys(josh.username)
        self.selenium.find_element_by_id('id_password').send_keys("password")
        self.selenium.find_element_by_id('login-btn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        self.selenium.get('%s%s' % (self.live_server_url, '/game/create/'))
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        self.selenium.find_element_by_id('generatePasswordBtn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        created_game = Game.objects.all().first()

        self.assertIsNotNone(created_game.password)

    def test_selenium_join_game_with_password(self):
        mike = self.create_michael_hilton()
        josh = self.create_josh_sunshine()

        # Create game with password
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.selenium.find_element_by_id(
            'id_username').send_keys(mike.username)
        self.selenium.find_element_by_id('id_password').send_keys("password")
        self.selenium.find_element_by_id('login-btn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        self.selenium.get('%s%s' % (self.live_server_url, '/game/create/'))
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        self.selenium.find_element_by_id('generatePasswordBtn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        generated_password = Game.objects.all().first().password

        # Logout current user, login alternative user
        self.selenium.find_element_by_id('leaveBtn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        self.selenium.find_element_by_id('logoutButton').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.selenium.find_element_by_id(
            'id_username').send_keys(josh.username)
        self.selenium.find_element_by_id('id_password').send_keys("password")
        self.selenium.find_element_by_id('login-btn').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))

        # Join game
        created_game = Game.objects.all().first()
        self.selenium.get('%s%s' % (self.live_server_url,
                                    '/game/{}/'.format(created_game.id)))
        self.selenium.find_element_by_id(
            'id_password').send_keys(generated_password)
        self.selenium.find_element_by_id('submit-pass').click()
        WebDriverWait(self.selenium, SeleniumTests.timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))
        josh_player = Player.objects.get(user=josh, game=created_game)

        self.assertIn(josh_player, created_game.game_players.all())
