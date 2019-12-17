# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from accounts.models import UnoUser

import uuid

class PendingFriendRequests(models.Model):
    sender = models.ForeignKey(UnoUser, on_delete=models.CASCADE, related_name="sender")
    recipient = models.ForeignKey(UnoUser, on_delete=models.CASCADE, related_name="recipient")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    # True action indicates that the friend request is being accepted. False, otherwise.
    action = models.BooleanField(default=True)