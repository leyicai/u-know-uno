# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from unoGame import models

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import UnoUser
from django.http import HttpResponse
from unoGame.models import DataTracker

import json

# Create your views here.


@login_required(login_url='home')
def homepage(request):
    online_players = list(UnoUser.objects.exclude(
        username__startswith='computer'))
    return render(request, 'gameTables/gameLobby.html', {"games": models.Game.objects.all(), 'user_list': online_players})


@login_required(login_url='home')
def reload_if_necessary(request):
    if DataTracker.SHOULD_RELOAD:
        # print("Reload necessary")
        DataTracker.SHOULD_RELOAD = False
        return HttpResponse(json.dumps({'shouldReload': True}), content_type='application/json')
    return HttpResponse(json.dumps({'shouldReload': False}), content_type='application/json')
