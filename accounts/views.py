# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from accounts.forms import LoginForm, RegisterForm, UpdateProfileForm
from accounts.models import UnoUser
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout as DjangoLogout
from django.contrib.auth.decorators import login_required
from unoGame.models import GameRecord, GamePlayerScore

# Create your views here.
REGISTER_ACTION = 'REGISTER'
LOGIN_ACTION = 'LOGIN'


def index(request):
    next_page = 'gameTables:homepage'
    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == REGISTER_ACTION:
                register_form = RegisterForm(request.POST)
                if register_form.is_valid():
                    user = register_form.save(commit=False)
                    user.set_password(register_form.cleaned_data['password1'])
                    # print(user.photo)
                    user.save()
                    login(request, user)
                    next_page = request.POST['next'] if 'next' in request.POST else next_page
                    return redirect(next_page)
                else:
                    login_form = LoginForm()
                    return render(request, 'accounts/index.html', {"register_form": register_form, "login_form": login_form, "next": next_page})
            elif action == LOGIN_ACTION:
                login_form = LoginForm(request.POST)
                if login_form.is_valid():
                    user = authenticate(
                        username=request.POST['username'], password=request.POST['password'])
                    if user:
                        login(request, user)
                        next_page = request.POST['next'] if 'next' in request.POST else next_page
                        return redirect(next_page)
                else:
                    register_form = RegisterForm()
                    return render(request, 'accounts/index.html', {"register_form": register_form, "login_form": login_form, "next": next_page})
    else:
        if request.user and request.user.is_authenticated:
            return redirect(next_page)
        next_page = request.GET['next'] if 'next' in request.GET else next_page
    login_form = LoginForm()
    register_form = RegisterForm()
    return render(request, 'accounts/index.html', {"register_form": register_form, "login_form": login_form, "next": next_page})


@login_required(login_url='home')
def profile(request):
    update_form = None
    if request.method == 'POST':
        update_form = UpdateProfileForm(
            request.POST, request.FILES, instance=request.user)
        if update_form.is_valid():
            user = request.user
            user.first_name = update_form.cleaned_data['first_name']
            user.last_name = update_form.cleaned_data['last_name']
            user.email = update_form.cleaned_data['email']
            user.gender = update_form.cleaned_data['gender']
            # user.username=update_form.cleaned_data['username']
            user.date_of_birth = update_form.cleaned_data['date_of_birth']
            user.photo = update_form.cleaned_data['photo']
            if update_form.cleaned_data['new_password'] and not user.check_password(update_form.cleaned_data['new_password']):
                user.set_password(update_form.cleaned_data['new_password'])
            user.save()
            return redirect('home')
        else:
            return render(request, 'accounts/profile.html', {'update_form': update_form})
    else:
        update_form = UpdateProfileForm(instance=request.user)
        return render(request, 'accounts/profile.html', {'update_form': update_form})


def logout(request):
    if request.user:
        DjangoLogout(request)
    return redirect('home')


@login_required(login_url='home')
def game_records(request):
    game_records = []
    records = list(GameRecord.objects.filter(
        player_scores__user__in=[request.user]))
    for record in records:
        temp_record = record.as_json()
        user_score = record.player_scores.filter(user=request.user).first()
        temp_record['score'] = user_score.score
        game_records.append(temp_record)
    return render(request, 'accounts/game_records.html', {'game_records': game_records})
