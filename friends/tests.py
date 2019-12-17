# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from accounts.models import UnoUser
from datetime import datetime
from django.test import Client, TestCase
from friends.models import PendingFriendRequests

class FriendRequestTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        super(FriendRequestTestCase, self).setUp()

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

    def test_create_friend_requests(self):
        josh = self.create_josh_sunshine()
        mike = self.create_michael_hilton()

        # Initiate Request from user 1
        self.client.force_login(josh)
        self.post_data = {'friendRequest': mike.username}
        self.client.post('/friends/friendRequest/', data=self.post_data)
        accept = PendingFriendRequests.objects.filter(sender=josh, recipient=mike, action=True).first()
        decline = PendingFriendRequests.objects.filter(sender=josh, recipient=mike, action=False).first()

        self.assertIsNotNone(accept)
        self.assertIsNotNone(decline)

    def test_accept_friend_requests(self):
        josh = self.create_josh_sunshine()
        mike = self.create_michael_hilton()

        # Initiate Request from user 1
        self.client.force_login(josh)
        self.post_data = {'friendRequest': mike.username}
        self.client.post('/friends/friendRequest/', data=self.post_data)
        # Accept Request from user 2
        self.client.logout()
        self.client.force_login(mike)
        accept = PendingFriendRequests.objects.filter(sender=josh, recipient=mike, action=True).first()
        self.client.post('/friends/processFriendRequest/{}'.format(accept.uuid))

        self.assertIn(josh, mike.friends.all())

    def test_decline_friend_requests(self):
        josh = self.create_josh_sunshine()
        mike = self.create_michael_hilton()

        # Initiate Request from user 1
        self.client.force_login(josh)
        self.post_data = {'friendRequest': mike.username}
        self.client.post('/friends/friendRequest/', data=self.post_data)
        # Decline Request from user 2
        self.client.logout()
        self.client.force_login(mike)
        decline = PendingFriendRequests.objects.filter(sender=josh, recipient=mike, action=False).first()
        self.client.post('/friends/processFriendRequest/{}'.format(decline.uuid))
        
        self.assertNotIn(josh, mike.friends.all())

