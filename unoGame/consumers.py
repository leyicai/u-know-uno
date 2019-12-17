""" All of the websocket actions for the game and chat functionalities"""
import json
import time
import threading

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from .models import Game, Player, UnoUser, Card, GameRecord, GamePlayerScore
from . import uno


class GameChatConsumer(WebsocketConsumer):
    def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = 'chat_%s' % self.game_id

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'username': text_data_json['username'],
                'message': message
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        print(event)

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'username': event['username'],
        }))


class GameConsumer(WebsocketConsumer):
    """Websocket for inside of the game"""

    def connect(self):
        """ connect
        create a Player for user if not created
        add the player into current game (check joinable status)
        add consumer into channel
        """
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = "game_%s" % game_id
        self.id = int(game_id)
        self.game = Game.objects.get_or_none(id=game_id)
        if not self.game:
            return
        self.user = self.scope["user"]
        self.player = Player.objects.get_or_none(
            user=self.user, game=self.game
        )
        print(self.user, "connect to game", game_id)
        if self.player:
            print("order:", self.player.order)

        if not self.player and self.game.password:
            return

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()
        self.join_game()

    def join_game(self):
        """ join_game
        user try to join a game.
        If successfully joined, create a corresponding player object
        and update game's joinable flag if necessary

        """
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        if not self.player and game.is_joinable:
            print(self.user, "join game")
            players = game.game_players.all()
            order = self.get_current_order(players)
            self.order = order
            player, _ = Player.objects.get_or_create(
                user=self.user, game=game, order=order)
            # self.player_id = player.id
            self.player = player
            game.update_joinable()
            self.game = game
        if game.is_started:
            self.init_cards(game)

        self.send_update_game()

    def disconnect(self, close_code):
        # Leave room group
        game = Game.objects.get_or_none(id=self.id)
        if game:
            player = Player.objects.get_or_none(
                user=self.scope['user'], game=game)
            if player:
                player.delete()
        self.send_update_game()
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        print(self.user, "recv", data)

        self.actions[data["action"]](self, data)

    # Game Actions
    def timeout(self, data):
        """timeout
        When a user timeout, automatically draw cards for this player
        """
        print("timeout")
        game = Game.objects.get_or_none(id=self.id)
        if game:
            player = Player.objects.get_or_none(user=self.user, game=game)
            if not player:
                return
            if game.draw_card != 0:
                # user draw penalty
                num = game.draw_card
                draw_cards = game.draw_cards(player, num)
                game.clear_draw_card()
            else:
                draw_cards = game.draw_cards(player, 1)
            current_player = game.update_current_player()
            own_cards = [c.as_json() for c in player.get_card_in_hand()]
            self.send_update_draw_card(
                draw_cards, own_cards, player.order, current_player.user.username, current_player.order)
            while "computer" in current_player.user.username:
                action, cards = game.computer_action()
                next_player = game.update_current_player()

                if action is "draw":
                    # computer draw a card. users got "update_draw_card"
                    own_cards = [c.as_json()
                                 for c in current_player.get_card_in_hand()]
                    self.send_update_draw_card(
                        cards, own_cards, current_player.order, next_player.user.username, current_player.order)

                elif action is "play" or action is "end" or action is "play_draw":
                    # computer play a card (not +2/+4). users got "update_play_card"
                    if len(cards) != 1:
                        print("computer play more than one card!!")
                    current_player = Player.objects.get_or_none(
                        id=current_player.id)
                    self.send_play_card(
                        cards[0], [
                        ], current_player.order, current_player.is_uno, next_player.user.username,
                        next_player.order)
                    if action is "end":
                        # this computer player wins
                        self.end_game(current_player.id)
                        break
                    elif action is "play_draw":
                        # computer play a (+2/+4). need to check if next player is able to stack card on it
                        current_player = next_player
                        if not current_player.can_play_draw():
                            # player automatically draw cards and skip
                            print(current_player, "draw penalty")
                            cards = game.draw_cards(
                                current_player, game.draw_card)
                            game.clear_draw_card()
                            own_cards = [c.as_json()
                                         for c in current_player.get_card_in_hand()]
                            next_player = game.update_current_player()
                            self.send_update_draw_card(
                                cards, own_cards, current_player.order, next_player.user.username, next_player.order)
                else:
                    print("computer action:", action, cards)
                current_player = next_player

    def get_ready(self, data):
        """ 
        When user click on "ready" button, change flag is_ready
        if game can start, (assign computer players,)
        init uno cards
        """
        print("get_ready")
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        self.game = game
        player = Player.objects.get_or_none(
            user=self.scope["user"],
            game=game
        )
        if not player:
            return
        player.is_ready = True
        player.save()
        self.player = player
        self.send_update_game()

        if game.can_start_game():
            player.is_current_player = True
            player.save()
            # self.init_game()
            game.init_game()
            self.send_update_game()
            self.send_init_cards()

    def draw_card(self, data):
        """ 
        When current player click on deck card, draw one card from deck
        """
        print(self.user, "draw card")
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        self.game = game
        player = Player.objects.get_or_none(
            user=self.scope["user"], game=self.game)
        if not player:
            return
        self.player = player
        game = Game.objects.get_or_none(id=self.id)
        if game and player.is_current_player:
            if game.draw_card != 0:
                print("Must play '+' cards!")
                return
            draw_cards = game.draw_cards(player, 1)
            if draw_cards is None:
                return
            current_player = game.update_current_player()
            own_cards = [c.as_json() for c in player.get_card_in_hand()]
            self.send_update_draw_card(
                draw_cards, own_cards, player.order, current_player.user.username, current_player.order)

            # computer action
            while "computer" in current_player.user.username:
                # print("computer:", current_player)
                action, cards = game.computer_action()
                next_player = game.update_current_player()

                if action is "draw":
                    # computer draw a card. users got "update_draw_card"
                    own_cards = [c.as_json()
                                 for c in current_player.get_card_in_hand()]
                    self.send_update_draw_card(
                        cards, own_cards, current_player.order, next_player.user.username, next_player.order)

                elif action is "play" or action is "end" or action is "play_draw":
                    # computer play a card (not +2/+4). users got "update_play_card"
                    if len(cards) != 1:
                        print("computer play more than one card!!")
                    current_player = Player.objects.get_or_none(
                        id=current_player.id)

                    self.send_play_card(
                        cards[0], [
                        ], current_player.order, current_player.is_uno, next_player.user.username,
                        next_player.order)
                    if action is "end":
                        # this computer player wins
                        self.end_game(current_player.id)
                        break
                    elif action is "play_draw":
                        # computer play a (+2/+4). need to check if next player is able to stack card on it
                        current_player = next_player
                        if not current_player.can_play_draw():
                            # player automatically draw cards and skip
                            print(current_player, "draw penalty")
                            cards = game.draw_cards(
                                current_player, game.draw_card)
                            game.clear_draw_card()
                            own_cards = [c.as_json()
                                         for c in current_player.get_card_in_hand()]
                            next_player = game.update_current_player()
                            self.send_update_draw_card(
                                cards, own_cards, current_player.order, next_player.user.username, next_player.order)
                else:
                    print("computer action:", action, cards)
                    self.send_update_game()
                current_player = next_player

    def play_card(self, data):
        """ 
        When current player click one one card in hand, play this card
        """
        # print(self.user, "play one card")
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        self.game = game
        player = Player.objects.get_or_none(
            user=self.scope["user"], game=self.game)
        if not player:
            return
        self.player = player
        if self.player.is_current_player:
            game = Game.objects.get_or_none(id=self.id)
            if not game:
                return
            play_card = Card.objects.get(id=data['card_id'])
            if game.draw_card != 0 and "draw" not in play_card.card_type:
                print("Must play '+' cards!")
                return
            card, own_cards = game.play_card(
                player, data['card_id'], data["choose_color"])
            if card is None:
                return
            current_player = game.update_current_player()
            self.send_play_card(card, own_cards, player.order,
                                player.is_uno, current_player.user.username, current_player.order)
            if len(own_cards) == 0:
                # player wins
                self.end_game(player.id)
                print("play_card: wins")
                return
            if len(own_cards) == 1:
                uno = True
            else:
                uno = False

            if game.draw_card != 0 and not current_player.can_play_draw():
                # player has to draw card
                cards = game.draw_cards(current_player, game.draw_card)
                game.clear_draw_card()
                own_cards = [c.as_json()
                             for c in current_player.get_card_in_hand()]
                next_player = game.update_current_player()
                self.send_update_draw_card(
                    cards, own_cards, current_player.order, next_player.user.username, next_player.order)
                current_player = next_player
            action = ""
            while "computer" in current_player.user.username:
                # print("computer:", current_player)
                action, cards = game.computer_action()
                next_player = game.update_current_player()

                if action is "draw":
                    # computer draw a card. users got "update_draw_card"
                    own_cards = [c.as_json()
                                 for c in current_player.get_card_in_hand()]
                    self.send_update_draw_card(
                        cards, own_cards, current_player.order, next_player.user.username, next_player.order)

                elif action is "play" or action is "play_uno" or action is "end" or action is "play_draw":
                    # computer play a card (not +2/+4). users got "update_play_card"
                    if len(cards) != 1:
                        print("computer play more than one card!!")
                    current_player = Player.objects.get_or_none(
                        id=current_player.id)
                    self.send_play_card(
                        cards[0], [
                        ], current_player.order, current_player.is_uno, next_player.user.username,
                        next_player.order)
                    if action is "end":
                        # this computer player wins
                        self.end_game(current_player.id)
                        break
                    elif action is "play_draw":
                        # print("computer play draw", cards)
                        # computer play a (+2/+4). need to check if next player is able to stack card on it
                        current_player = next_player
                        if not current_player.can_play_draw():
                            # player automatically draw cards and skip
                            print(current_player, "draw penalty")
                            cards = game.draw_cards(
                                current_player, game.draw_card)
                            game.clear_draw_card()
                            own_cards = [c.as_json()
                                         for c in current_player.get_card_in_hand()]
                            next_player = game.update_current_player()
                            self.send_update_draw_card(
                                cards, own_cards, current_player.order, next_player.user.username, next_player.order)
                else:
                    print("computer action:", action, cards)
                    self.send_update_game()

                current_player = next_player
                if uno:
                    threading.Thread(target=self.uno_timer).start()

    def call_uno(self, data):
        """ 
        User call uno. 
        Set is_uno = T when all requirements satisfied:
        1. Player has only one card in hand
        2. Player is current player
        """
        print(self.user, "call uno")
        game = Game.objects.get_or_none(id=self.id)
        if game:
            player = Player.objects.get_or_none(
                user=self.scope["user"], game=game)
            if player:
                player.is_uno = True
                player.save()
                current_player = game.get_current_player()
                self.send_update_uno(
                    player.order, current_player.user.username, current_player.order)

    def get_current_order(self, players):
        orders = [1, 2, 3, 4]
        for player in players:
            if player.order in orders:
                orders.remove(player.order)
        return orders[0]

    def init_game(self):
        """ 
        Assign computer player(s) if needed
        Init deck cards; Draw a current card from deck;
        Assign cards for players
        """
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        self.game = game

        # assign computer players
        computer_needed = 4 - game.game_players.count()
        while computer_needed > 0:
            game.get_computer_player(
                "computer" + str(computer_needed)
            )
            computer_needed -= 1
        print("init cards for game", self.id)
        deck = uno.create_deck()
        # draw a current card from deck
        current_card = uno.get_cards(deck, 1)[0]
        c = Card.objects.create(color=current_card['color'], card_type=current_card['card_type'],
                                game=game, is_on_deck=False, is_current_card=True)
        c.save()

        # assign cards for all players
        for player in game.game_players.all():
            init_cards = uno.get_cards(deck, 7)
            for card in init_cards:
                c = Card.objects.create(color=card['color'], card_type=card['card_type'],
                                        game=game, is_on_deck=False, is_current_card=False, owner=player)
                c.save()

        # save deck cards into db
        for card in deck:
            c = Card.objects.create(color=card['color'], card_type=card['card_type'],
                                    game=game, is_on_deck=True, is_current_card=False)
            c.save()

    def leave_game(self, data):
        """ leave_game
        When someone click on "leave", apply penalty and automatically end this game
        """
        user = self.scope["user"]
        print(self.user, "leave game")
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        player = Player.objects.get_or_none(user=user, game=game)
        if not player:
            return
        player.delete()
        if game.is_started:
            time.sleep(3)
            # apply penalty. ?validator in account.models
            user.score -= 50
            user.save()
            # generate leave game record
            result = user.username + " left the game!"
            game_record = GameRecord(
                game_id=self.id,
                result=result,
                winner=None
            )
            game_record.save()
            for player in game.game_players.all():
                player_score = GamePlayerScore.objects.create(
                    game_id=game.id, user=player.user, score=0)
                print(player_score)
                game_record.player_scores.add(player_score)
                print("Added player score")
            # Want to keep track of the user that left the game as well.
            user_game_score = GamePlayerScore.objects.create(
                game_id=game.id, user=UnoUser.objects.get(username=user.username), score=-50)
            game_record.player_scores.add(user_game_score)
            game_record.save()
            # self.send_leave_game()
            self.send_end_game("")
            game.delete()
        else:
            self.send_update_game()
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def uno_timer(self):
        """ 
        Uno timer in a new thread.
        If user fails to call uno within the countdown, apply penalty
        """
        i = 0.0
        while i < 5:
            time.sleep(0.5)
            i += 0.5
            player = Player.objects.get_or_none(
                user=self.scope["user"], game=self.game)
            if not player:
                return
            self.player = player
            if player.is_uno:
                return
        # apply penalty
        print("uno penalty")
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        self.game = game
        deck = [card.as_json() for card in game.get_deck()]
        # 2 cards penalty
        cards = uno.get_cards(deck, 2)
        # print(cards)
        for card in cards:
            c = Card.objects.get_or_none(id=card['id'])
            if c != None:
                c.set_owner(self.player)
        if self.player:
            self.player.is_uno = False
            self.player.save()
            current_player = game.get_current_player()
            own_cards = [c.as_json() for c in self.player.get_card_in_hand()]
            self.send_update_draw_card(
                cards, own_cards, self.player.order, current_player.user.username, current_player.order)

    def end_game(self, winner_id):
        """ 
        One player wins the game. 
        Generate game record and send to all.
        """
        # Update score for each user
        print(winner_id)
        winner = Player.objects.get_or_none(id=winner_id)
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        result = ""
        win_points = 0
        print(winner.user.username, "wins game", self.id)
        player_scores = []
        for player in game.game_players.all():
            cards = [card.as_json() for card in player.get_card_in_hand()]
            score = uno.get_score(cards)
            win_points += score
            if not player.id is winner_id:
                result += (player.user.username + "-" + str(score) + "\n")
                if "computer" in player.user.username:
                    continue
                score = -1 * score
                player.user.score += score
                player.user.save()
                player_score = GamePlayerScore.objects.create(
                    game_id=self.id, user=player.user, score=score)
                player_scores.append(player_score)
        result += (winner.user.username + "+" + str(win_points) + "\n")
        if not "computer" in winner.user.username:
            winner.user.score += win_points
            player_score = GamePlayerScore.objects.create(
                game_id=self.id, user=winner.user, score=win_points)
            player_scores.append(player_score)
            winner.user.save()
        print(result)
        game_record = GameRecord(
            game_id=self.id, result=result, winner=winner.user)
        game_record.save()
        for p_score in player_scores:
            print(p_score)
            game_record.player_scores.add(p_score)
        game_record.save()
        game.delete()
        self.send_end_game(winner.user.username)

    # ASYNC TO SYNC ACTIONS
    def send_update_game(self):
        """ 
        Sends all update game info as a json object when there's an update
        """
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        current_player = game.get_current_player()
        if not current_player:
            current_player = ""
            current_player_order = 0
        else:
            current_player_order = current_player.order
            current_player = current_player.user.username
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "update_game",
                "game": game.as_json(),
                "current_player": current_player,
                "current_player_order": current_player_order,
            }
        )

    def send_update_uno(self, order, current_player, current_player_order):
        """ 
        Inform all players when someone called uno
        """
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "update_uno",
                "player": order,
                "current_player": current_player,
                "current_player_order": current_player_order,
            }
        )

    def send_init_cards(self):
        """ 
        Send initial cards info to all player
        """
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        current_player = game.get_current_player()
        current_player_order = current_player.order
        current_player = current_player.user.username
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "init_cards",
                "game": game.as_json(),
                "current_player": current_player,
                "current_player_order": current_player_order,
            }
        )

    def send_update_draw_card(self, cards, own_cards, order, current_player, current_player_order):
        """ 
        Send update when one player (with the order) draw cards from deck
        @cards is a list of card json objects
        @current_player is the username of current player in game
        """
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "update_draw_card",
                "player": order,
                "cards": cards,
                "own_cards": own_cards,
                "number": len(cards),
                "current_player": current_player,
                "current_player_order": current_player_order,
            }
        )

    def send_play_card(self, card, own_cards, order, uno, current_player, current_player_order):
        """ 
        Send update when one player(with the order) played one card
        @own_cards is cards of the player with 'order'
        @uno is the uno status of the player with 'order'
        @current_player is the username of current player in game
        """
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "update_play_card",
                "card": card,
                "own_cards": own_cards,
                "player": order,
                "uno": uno,
                "current_player": current_player,
                "current_player_order": current_player_order,
            }
        )

    def send_leave_game(self):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "leave_game",
                # "player": self.user.username
            }
        )

    def send_end_game(self, winner):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "update_end_game",
            }
        )

    # Send Data To WebSocket
    def update_game(self, game):
        # print(self.user, "update game:",
        #       json.dumps(game, indent=2))
        self.send(text_data=json.dumps(game))

    def update_end_game(self, data):
        self.send(text_data=json.dumps({
            'type': "end_game"
        }))

    def init_cards(self, data):
        player = Player.objects.get_or_none(
            user=self.scope["user"], game=self.game)
        if not player:
            return
        self.player = player
        game = Game.objects.get_or_none(id=self.id)
        if not game:
            return
        current_player = game.get_current_player()
        init_cards = {
            'type': 'init_cards',
            'init_cards': [card.as_json() for card in player.get_card_in_hand()],
            "current_player": current_player.user.username,
            "current_player_order": current_player.order,
        }
        self.send(text_data=json.dumps(init_cards))

    def update_draw_card(self, data):
        """ 
        data: {
            "draw_player": order (int),
            "cards": cards,
            "number": len(cards),
            "current_player": current_player (username)
        }
        """
        # print(time.asctime(time.localtime(time.time())),self.user, "update draw cards:",
        #       json.dumps(data, indent=2))
        if str(data['player']) == str(self.player.order) and "cards" in data:
            self.send(text_data=json.dumps({
                "type": "draw_card",
                "added_cards": data["cards"],
                "own_cards": data["own_cards"],
                "current_player": data["current_player"],
                "current_player_order": data["current_player_order"],
            }))
        else:
            self.send(text_data=json.dumps(data))
        time.sleep(len(data["cards"]))

    def update_play_card(self, data):
        """ 
        data:{
            "card": card,
            "own_cards": own_cards,
            "player": order,
            "uno": uno,
            "current_player": current_player.user.username,
        }
        """
        # print(time.asctime(time.localtime(time.time())),self.user, "update play card:",
        #       json.dumps(data, indent=2))
        if str(data['player']) == str(self.player.order) and "own_cards" in data:
            self.send(text_data=json.dumps({
                "type": "play_card",
                "card": data["card"],
                "own_cards": data["own_cards"],
                "current_player": data["current_player"],
                "current_player_order": data["current_player_order"],
            }))
        else:
            self.send(text_data=json.dumps(data))
        time.sleep(1)

    def update_uno(self, data):
        self.send(text_data=json.dumps(data))

    actions = {
        "getReady": get_ready,
        "drawOneCard": draw_card,
        "playOneCard": play_card,
        "callUno": call_uno,
        "leaveGame": leave_game,
        "timeout": timeout,
    }
