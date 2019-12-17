# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from accounts.models import UnoUser
import time
from . import uno

# Create your models here.


class DataTracker(object):
    SHOULD_RELOAD = False


class GetOrNoneManager(models.Manager):
    """Adds get_or_none method to objects"""

    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class Game(models.Model):
    # status
    is_started = models.BooleanField(default=False)
    is_joinable = models.BooleanField(default=True)
    password = models.CharField(max_length=10, default="")
    creator = models.ForeignKey(UnoUser, on_delete=models.CASCADE)
    is_reverse = models.BooleanField(default=False)
    draw_card = models.IntegerField(default=0)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ['-id']

    def as_json(self):
        return dict(
            game_id=self.id,
            is_started=self.is_started,
            is_joinable=self.is_joinable,
            is_reverse=self.is_reverse,
            current_card=self.get_current_card().as_json() if self.get_current_card() else None,
            players=[
                player.as_json() for player in self.game_players.all()
            ],
            password=self.password,
        )

    def get_current_card(self):
        current_card = Card.objects.filter(game=self, is_current_card=True)
        if current_card.count() == 0:
            return None
        return current_card[0]

    def get_deck(self):
        return Card.objects.filter(game=self, is_on_deck=True)

    def can_start_game(self):
        # check if all players in game has been ready
        for player in self.game_players.all():
            if not player.is_ready:
                return False
        # can start; start the game
        self.is_started = True
        self.is_joinable = False
        self.save()
        return True

    def update_joinable(self):
        # check if the game is joinable and change if necessary
        if self.game_players.count() == 4:
            self.is_joinable = False
        elif self.is_started is True:
            self.is_joinable = False
        else:
            self.is_joinable = True
        self.save()

    def get_current_player(self):
        current_player = Player.objects.filter(
            game=self, is_current_player=True)
        if current_player.count() >= 1:
            return current_player.reverse()[0]
        else:
            return None

    def update_current_player(self):
        current_player = Player.objects.filter(
            game=self, is_current_player=True)
        if current_player.count() != 1:
            print(current_player)
        current_player = current_player[0]
        order = current_player.order
        if current_player:
            current_player.is_current_player = False
            current_player.save()
            next_order = 0
            if self.is_reverse:
                next_order = order - 1
                if next_order == 0:
                    next_order = 4
            else:
                next_order = order % 4 + 1
            next_player = Player.objects.filter(game=self, order=next_order)[0]
            next_player.is_current_player = True
            next_player.save()
            return next_player

    def add_draw_card(self, num):
        """ 
        Accumulate draw cards' number
        """
        self.draw_card += num
        self.save()

    def clear_draw_card(self):
        self.draw_card = 0
        self.save()

    def get_current_order(self):
        orders = [1, 2, 3, 4]
        for player in self.game_players.all():
            if player.order in orders:
                orders.remove(player.order)
        return orders[0]

    def get_computer_player(self, username):
        computer_user, _ = UnoUser.objects.get_or_create(
            username=username)
        computer_user.save()
        order = self.get_current_order()
        computer_player, _ = Player.objects.get_or_create(
            user=computer_user, game=self, is_current_player=False, order=order)
        computer_player.save()
        return computer_player

    def init_game(self):
        # assign computer players
        computer_needed = 4 - self.game_players.count()
        while computer_needed > 0:
            self.get_computer_player("computer" + str(computer_needed))
            computer_needed -= 1
        deck = uno.create_deck()
        # draw a current card from deck
        current_card = uno.get_cards(deck, 1)[0]
        while current_card["card_type"] not in uno.NUMBERS:
            # init card can only be number cards
            deck.append(current_card)
            current_card = uno.get_cards(deck, 1)[0]

        c = Card.objects.create(color=current_card['color'], card_type=current_card['card_type'],
                                game=self, is_on_deck=False, is_current_card=True)
        c.save()
        # current_card['id'] = c.id

        # assign cards for all players
        for player in self.game_players.all():
            init_cards = uno.get_cards(deck, 7)
            for card in init_cards:
                c = Card.objects.create(color=card['color'], card_type=card['card_type'],
                                        game=self, is_on_deck=False, is_current_card=False, owner=player)
                c.save()

        # save deck cards into db
        for card in deck:
            c = Card.objects.create(color=card['color'], card_type=card['card_type'],
                                    game=self, is_on_deck=True, is_current_card=False)
            c.save()

    def draw_cards(self, player, num):
        """ 
        Player draw 'num' cards from deck
        @return cards the player drew (json obj)
        """
        if player.game != self or not player.is_current_player:
            return []
        deck = [card.as_json() for card in self.get_deck()]
        # draw cards
        print(player.user.username, "draw", num, "cards")
        cards = uno.get_cards(deck, num)
        for card in cards:
            c = Card.objects.get_or_none(id=card['id'])
            if c != None:
                # c.set_owner(player)
                c.is_on_deck = False
                c.is_current_card = False
                c.owner = player
                c.save()
        player.is_uno = False
        player.save()
        return cards

    def play_card(self, player, play_card_id, choose_color):
        """ 
        Player play a card with 'play_card_id'
        @return play_card, own_cards
        @play_card: json obj of the played card
        @own_cards: list of json objs currently in the player's hand
        """
        play_card = Card.objects.get(id=play_card_id)
        current_card = self.get_current_card()
        if uno.matchCard(play_card.as_json(), current_card.as_json()):
            print(player.user.username, "play card",
                  play_card.color, play_card.card_type, choose_color)
            play_card.set_current()
            current_card.set_deck()
            card = play_card.as_json()
            current_card = play_card
            # TODO: action and wild cards
            if card['color'] == 'wild' and choose_color != "":
                # TODO: wild cards. choose new color
                print(player.user.username, "play wild card")
                current_card.temp_color = choose_color
                current_card.save()
                card['color'] = choose_color
                # current_card['temp_color'] = choose_color
                if card['card_type'] == "draw4":
                    self.add_draw_card(4)
            elif card['card_type'] == 'skip':
                # skip a player
                self.update_current_player()
            elif card['card_type'] == 'reverse':
                # reverse cycle
                self.is_reverse = not self.is_reverse
                self.save()
            elif card['card_type'] == 'draw2':
                # TODO: user play draw2
                self.add_draw_card(2)
            return card, [c.as_json() for c in player.get_card_in_hand()]
        print("not match", play_card.as_json(), current_card.as_json())
        return None, None

    def computer_action(self):
        """ 
        If current user is a computer, perform a round for the computer
        @return: action("play"/"draw"/"play_draw"/"end"), cards(list of card json obj)
        """
        player = Player.objects.filter(
            game=self, is_current_player=True)
        if player.count() != 1:
            if player.count() < 1:
                return None, None
        player = player[0]
        if "computer" not in player.user.username:
            return None, None
        if self.draw_card != 0:
            # computer draw cards for previous penalties
            draw_cards = self.draw_cards(player, self.draw_card)
            self.clear_draw_card()
            return "draw", draw_cards

        # computer try to play card
        current_card = self.get_current_card()
        hand_cards = player.get_card_in_hand()
        action = ""
        play_card = None
        for card in hand_cards:
            if uno.matchCard(card.as_json(), current_card.as_json()):
                # current_card.delete()
                action = "play"
                current_card.set_deck()
                # current_card.is_on_deck = True
                # current_card.is_current = False
                # current_card.owner = None
                # current_card.save()
                card.set_current()
                # card.is_current = True
                # card.is_on_deck = False
                # card.owner = None
                # card.save()

                current_card = card
                play_card = card.as_json()
                # TODO: wild and action cards
                print(player.user.username, "play card",
                      play_card["color"], play_card["card_type"])
                if play_card['color'] == 'wild':
                    # TODO: wild cards. choose new color
                    current_card.temp_color = uno.get_random_color()
                    current_card.save()
                    play_card["color"] = current_card.temp_color
                    play_card["temp_color"] = play_card["color"]
                    print("computer play wild card, color:",
                          play_card["color"])
                    if play_card["card_type"] == "draw4":
                        self.add_draw_card(4)
                        action = "play_draw"
                elif play_card['card_type'] == 'skip':
                    # skip a player
                    self.update_current_player()

                elif play_card['card_type'] == 'reverse':
                    # reverse card
                    self.is_reverse = not self.is_reverse
                    self.save()

                elif play_card['card_type'] == 'draw2':
                    # TODO: draw 2
                    self.add_draw_card(2)
                    action = "play_draw"

                if player.get_card_in_hand().count() == 1:
                    print("*****************", player.user.username, "uno")
                    player.is_uno = True
                    player.save()
                if player.get_card_in_hand().count() == 0:
                    action = "end"
                    # this player wins
                break
        if play_card == None:
            # computer draw a card
            # print(player.user.username, "draw a card")
            cards = self.draw_cards(player, 1)
            return "draw", cards
        else:
            # computer played a card
            return action, [play_card, ]


class Player(models.Model):
    game = models.ForeignKey(
        Game, related_name="game_players", on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(UnoUser, on_delete=models.CASCADE, null=True)
    is_current_player = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False)
    is_uno = models.BooleanField(default=False)
    order = models.SmallIntegerField(default=0)  # range from 1 to 4

    objects = GetOrNoneManager()

    def __str__(self):
        return self.user.username

    def as_json(self):
        return dict(
            player_id=self.id,
            username=self.user.username,
            order=self.order,
            uno=self.is_uno,
            is_current_player=self.is_current_player,
            is_ready=self.is_ready,
            score=self.user.score,
            photo=self.user.photo,
            friends=[user.username for user in self.user.friends.all()],
        )

    def get_card_in_hand(self):
        return Card.objects.filter(game=self.game, owner=self, is_on_deck=False, is_current_card=False)

    def can_play_draw(self):
        current_card = self.game.get_current_card()
        if "draw" not in current_card.card_type:
            print("player.can_play_draw: error! current is not a +2/+4 card")
            return True
        hand_cards = [card.as_json() for card in self.get_card_in_hand()]
        return uno.can_play_draw(hand_cards, current_card.as_json())


class Card(models.Model):
    # card content
    color = models.CharField(max_length=10)
    temp_color = models.CharField(max_length=10, null=True, default="")
    card_type = models.CharField(max_length=20)
    # card game info
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="game_cards")
    is_on_deck = models.BooleanField()
    is_current_card = models.BooleanField()
    owner = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="player_cards", null=True)

    objects = GetOrNoneManager()

    class Meta:
        ordering = ['game', 'color', 'card_type']

    def __str__(self):
        return "Game "+str(self.game.id)+": "+self.color + " " + self.card_type

    def as_json(self):
        return dict(
            id=self.id,
            color=self.color,
            temp_color=self.temp_color,
            card_type=self.card_type,
            img_src="img/unoGame/unoCards/{0}_{1}.png".format(
                self.color, self.card_type)
        )

    def set_current(self):
        """ 
        set the card as current card of game
        """
        self.is_on_deck = False
        self.is_current_card = True
        self.owner = None
        self.save()

    def set_owner(self, player):
        """ 
        set the card's owner as player
        """
        self.is_on_deck = False
        self.is_current_card = False
        self.owner = player
        self.save()

    def set_deck(self):
        """ 
        set the card on_deck as true
        """
        self.is_on_deck = True
        self.is_current_card = False
        self.owner = None
        self.save()


class GamePlayerScore(models.Model):
    game_id = models.IntegerField()
    user = models.ForeignKey(UnoUser, on_delete=models.CASCADE)
    score = models.IntegerField()


class GameRecord(models.Model):
    game_id = models.IntegerField()
    winner = models.ForeignKey(
        UnoUser, null=True, related_name="win_games", on_delete=models.SET_NULL)
    player_scores = models.ManyToManyField(GamePlayerScore)
    result = models.CharField(max_length=300)
    time = models.DateTimeField(auto_now_add=True)
    objects = GetOrNoneManager()

    def as_json(self):
        winner = self.winner if self.winner != None else '-'
        player_list = []
        for player_score in self.player_scores.all():
            player_list.append(player_score.user)
        users = ", ".join([x.username for x in player_list])
        return {'winner': winner,
                'users': users,
                'result': self.result,
                'time': self.time,
                }


@receiver(post_save, sender=Game)
def game_post_save_handler(sender, instance, created, **kwargs):
    # print('received save signal')
    DataTracker.SHOULD_RELOAD = True


@receiver(pre_delete, sender=Game)
def game_post_delete_handler(sender, instance, **kwargs):
    # print('received delete signal')
    DataTracker.SHOULD_RELOAD = True
