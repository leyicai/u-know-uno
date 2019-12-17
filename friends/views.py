# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect
from unoGame.models import Game
from accounts.models import UnoUser
from .models import PendingFriendRequests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import json, os
# Create your views here.


def sendGameInvitationEmail(sender, recipient, game_id):
    game = Game.objects.get_or_none(id=game_id)
    if not game:
        return
    subject = "Join {} in an Uno Game!".format(sender.username)

    html_message = '''
    <h2 style="color: #2e6c80;"><span style="color: #000000;">Hello {},</span></h2>
    <p>&nbsp;</p>
    <p>Your friend, {} has invited you to play an uno game!</p>
    <p>Click <a href={}>here</a> to join the game!</p>
    {}
    <p>&nbsp;</p>
    <p>Enjoy the game!</p>
    <p>UKnow Uno Admin</p>
    <p>&nbsp;</p>
    '''
    link = 'http://127.0.0.1:8000/game/{}/beforeGame'.format(game_id)
    additional_text = ''
    if game.password:
        additional_text = '<p>The password to join the game is: {}</p>'.format(
            game.password)

    html_message = html_message.format(
        recipient.username, sender.username, link, additional_text)
    # recipient_email = (recipient.email,)
    # email = EmailMessage(
    #     subject=subject, body=html_message, to=recipient_email)
    # email.content_subtype = 'html'
    # email.send()
    
    message = Mail(
        from_email='donotreply@u-know-uno.herokuapp.com',
        to_emails=recipient.email,
        subject=subject,
        html_content=html_message
    )
    try:
        sg = SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
        sg.send(message)
    except Exception as e:
        print(e.message)


def sendFriendRequestEmail(sender, recipient, accept_uuid, decline_uuid):
    subject = "{} wants to add you as a friend!".format(sender.username)
    html_message = '''
    <h2 style="color: #2e6c80;"><span style="color: #000000;">Hello {},</span></h2>
    <p>&nbsp;</p>
    <p>Another player, {}, wants to add you as a friend!</p>
    <p><a href={}><button style="color: green;">Accept</button></a> <a href={}><button style="color: red;">Decline</button></a></p>
    <p>UKnow Uno Admin</p>
    <p>&nbsp;</p>
    '''
    accept_link = 'https://u-know-uno.herokuapp.com/friends/processFriendRequest/{}'.format(accept_uuid)
    decline_link = 'https://u-know-uno.herokuapp.com/processFriendRequest/{}'.format(decline_uuid)
    html_message = html_message.format(recipient.username, sender.username, accept_link, decline_link)
    # recipient_email = (recipient.email,)
    
    # email = EmailMessage(
    #     subject=subject, body=html_message, to=recipient_email)
    # email.content_subtype = 'html'
    # email.send()
    message = Mail(
        from_email='donotreply@u-know-uno.herokuapp.com',
        to_emails=recipient.email,
        subject=subject,
        html_content=html_message
    )
    try:
        sg = SendGridAPIClient(os.environ['SENDGRID_API_KEY'])
        sg.send(message)
    except Exception as e:
        print(e.message)

@login_required(login_url='home')
def friendRequest(request):
    sender = request.user
    recipient = UnoUser.objects.filter(username=request.POST['friendRequest']).first()
    if not recipient or recipient == sender:
        return
    # Assumes there are 2 requests (one for accept, one for decline) or none at all.
    existing_pending_requests = list(PendingFriendRequests.objects.filter(sender=sender, recipient=recipient).all())
    if existing_pending_requests != []:
        accept_request = existing_pending_requests[0] if existing_pending_requests[0].action else existing_pending_requests[1]
        decline_request = existing_pending_requests[1] if accept_request == existing_pending_requests[0] else existing_pending_requests[0]
        accept_uuid = accept_request.uuid
        decline_uuid = decline_request.uuid
    else:
        accept_uuid = PendingFriendRequests.objects.create(sender=sender, recipient=recipient).uuid
        decline_uuid = PendingFriendRequests.objects.create(sender=sender, recipient=recipient, action=False).uuid
    sendFriendRequestEmail(sender, recipient, accept_uuid, decline_uuid)
    return redirect('gameTables:homepage')

@login_required(login_url='home')
def processFriendRequest(request, uuid):
    pendingRequest = PendingFriendRequests.objects.filter(uuid=uuid).first()
    if not pendingRequest or pendingRequest.recipient != request.user:
        return redirect('home')
    with transaction.atomic():
        if pendingRequest.action:
            if pendingRequest.recipient not in list(pendingRequest.sender.friends.all()):
                pendingRequest.sender.friends.add(pendingRequest.recipient)
            if pendingRequest.sender not in list(pendingRequest.recipient.friends.all()):
                pendingRequest.recipient.friend.add(pendingRequest.sender)
            pendingRequest.sender.save()
            pendingRequest.recipient.save()
        PendingFriendRequests.objects.filter(sender=pendingRequest.sender, recipient=pendingRequest.recipient).all().delete()
    return redirect('home')


@login_required(login_url='home')
def getProfile(request):
    user_Profile = UnoUser.objects.filter(username=request.POST['profile_username']).first()
    profile_birthday = user_Profile.date_of_birth
    profile_birthday.strftime('%Y-%m-%d')
    profile_gender = user_Profile.gender
    profile_score = user_Profile.score
    profile_photo = user_Profile.photo
    data = {'username': request.POST['profile_username'], 'birthday': profile_birthday,
            'gender': profile_gender, 'score': profile_score, 'photo': profile_photo}
    return HttpResponse(json.dumps(data, default=str), content_type='application/json')
