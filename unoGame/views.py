# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from unoGame.models import Game, Player, Card, GameRecord
from accounts.models import UnoUser
from django.forms import model_to_dict
from . import uno
import json, string, random
from django.http import HttpResponse
from django.urls import reverse
from unoGame.forms import ValidateGamePasswordForm
from friends.views import sendGameInvitationEmail, friendRequest

# Create your views here.

@login_required(login_url='home')
def createGame(request):
    # in single mode, game automatically starts and doesn't accept new join
    game = Game(is_started=False, is_joinable=True, creator=request.user)
    game.save()
    # return redirect('unoGame:beforeGame', game_id=game.id)
    return redirect('unoGame:inGame', game_id=game.id)


@login_required(login_url='home')
def beforeGameAuth(request, game_id):
    print("Auth page for game: {}".format(game_id))
    game = Game.objects.get_or_none(id=game_id)
    if game != None:
        player = Player.objects.get_or_none(user=request.user, game=game)
        if game.password and not player:
            password_form = ValidateGamePasswordForm()
            return render(request, 'unoGame/gameAuth.html', {'password_form': password_form})
        else:
            return redirect('unoGame:inGame', game_id=game_id)
    else:
        return redirect('gameTables:homepage')

@login_required(login_url="home")
def validatePassword(request, game_id):
    game = Game.objects.get_or_none(id=game_id)
    if game != None:
        print(game.password)
        password_form = ValidateGamePasswordForm(request.POST)
        if password_form.is_valid() and game.password == password_form.cleaned_data['password']:
            count = game.game_players.all().count()
            player = Player.objects.get_or_create(user=request.user, game=game, order=count+1)
            return HttpResponse(json.dumps({'status': 'AUTHENTICATED'}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'status': 'FAILED'}), content_type='application/json')
        

@login_required(login_url='home')
def leaveGame(request, game_id):
    game = Game.objects.get_or_none(id=game_id)
    if game != None:
        game.delete()
    return redirect('gameTables:homepage')

def randomStringOfLength(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

@login_required(login_url='home')
def generatePassword(request, game_id):
    game = Game.objects.get_or_none(id=game_id)
    if game != None and not game.password:
        player = Player.objects.get_or_create(user=request.user, game=game)
        game.password = randomStringOfLength(3)
        game.save()
        resp = json.dumps(game.as_json())
        return HttpResponse(resp, content_type="application/json")
    else:
        return HttpResponse(json.dumps({}), content_type="application/json")
    

@login_required(login_url='home')
def inGame(request, game_id):
    # TODO: check if the game is joinable
    game = Game.objects.get_or_none(id=game_id)
    is_creator = False
    if game:
        is_creator = game.creator == request.user
        player = Player.objects.get_or_none(user=request.user, game=game)
        if game.password and not player:
            return redirect('unoGame:beforeGameAuth', game_id=game_id)
        return render(request, 'unoGame/uno.html', context={'password': game.password, 'is_creator': is_creator})
    return redirect('gameTables:homepage')


@login_required(login_url='home')
def endGame(request, game_id):
    game_record = GameRecord.objects.get_or_none(game_id=game_id)
    context = {}
    if game_record:
        if game_record.winner:
            if game_record.winner.username == request.user.username:
                context['img_src'] = "img/unoGame/winPicture.png"
                context["message"] = "Congrats! You win the game!"
            else:
                context['img_src'] = "img/unoGame/snorlax.png"
                context["message"] = "Oops! %s wins the game!" % (
                    game_record.winner.username)
        else:
            # someone leave game
            context["img_src"] = "img/unoGame/leaveGame.png"
            context["message"] = "Sorry...Someone has left the game. Game is Over..."

    return render(request, 'unoGame/endGamePage.html', context=context)


def chooseColor(request, id):
    return render(request, 'unoGame/chooseColor.html', {"id": id})


def showRules(request):
    return render(request, 'unoGame/gameRule.html')
