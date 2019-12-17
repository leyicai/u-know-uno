# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

from gameTables.models import Table

# Create your models here.
PLATINUM = 1000
DIAMOND = 500
GOLD = 250
SILVER = 100
BRONZE = 50


class UnoUser(AbstractUser):
    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('NONBINARY', 'Non Binary'),
    )
    photo = models.CharField(default='img/photos/anon_user.png', max_length=100)
    date_of_birth = models.DateField(default=datetime.date(2000, 4, 13))
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default='MALE')
    current_table = models.ForeignKey(
        Table, null=True, on_delete=models.SET_NULL)
    score = models.IntegerField(default=0, validators=[MinValueValidator(0), ])
    friends = models.ManyToManyField("self")

    def __str__(self):
        return self.username

    def rank(self):
        if self.score > PLATINUM:
            return 'PLATINUM'
        elif self.score > DIAMOND:
            return 'DIAMOND'
        elif self.score > GOLD:
            return 'GOLD'
        elif self.score > SILVER:
            return 'SILVER'
        elif self.score > BRONZE:
            return 'BRONZE'
        else:
            return 'NONE'
