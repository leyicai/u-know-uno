# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
# from django.contrib.auth.admin import UserAdmin
from accounts.models import UnoUser

admin.site.register(UnoUser)