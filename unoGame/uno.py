# Reference: https://github.com/bennuttall/uno/blob/master/uno.py
from random import shuffle, choice, seed
from itertools import product, repeat, chain
from datetime import datetime

seed(datetime.now())
COLORS = ['red', 'yellow', 'green', 'blue']
ALL_COLORS = COLORS + ['wild']
NUMBERS = list(range(0, 10)) + list(range(1, 10))
SPECIAL_CARD_TYPES = ['skip', 'reverse', 'draw2']
COLOR_CARD_TYPES = NUMBERS + SPECIAL_CARD_TYPES * 2
BLACK_CARD_TYPES = ['change', 'draw4']
CARD_TYPES = NUMBERS + SPECIAL_CARD_TYPES + BLACK_CARD_TYPES


def create_deck():
    """
    Return a list of the complete set of Uno Cards. 
    Card is represent as a json object 
    {
        "color": color(str),
        "card_type": card_type(str)
    }
    """
    color_cards = product(COLORS, COLOR_CARD_TYPES)
    black_cards = product(repeat('wild', 4), BLACK_CARD_TYPES)
    all_cards = chain(color_cards, black_cards)
    # all_cards = color_cards
    deck = [dict(color=color, card_type=card_type)
            for color, card_type in all_cards]
    shuffle(deck)
    return deck


def get_cards(deck, n):
    """
    Return a list of n Uno Cards pop from deck
    """
    shuffle(deck)
    return [deck.pop() for i in range(n)]


def get_random_color():
    """ 
    Return a random color
    """
    return choice(COLORS)


def matchCard(card, current_card):
    """ 
    check if card and current_card can match
    """
    return (
        card['color'] == current_card['temp_color'] or
        card['color'] == current_card['color'] or
        card['card_type'] == current_card['card_type'] or
        card['color'] == 'wild'
    )


def match_draw_card(card, current_card):
    """ 
    Check if card and current_card can match
    current_card here is either +2 or +4
    """
    if current_card["card_type"] == "draw4":
        return (
            card["card_type"] == "draw4" or
            (card["card_type"] == "draw2" and
             card["color"] == current_card["temp_color"])
        )
    elif current_card["card_type"] == "draw2":
        return "draw" in card["card_type"]
    else:
        return matchCard(card, current_card)


def can_play_draw(cards, current_card):
    """
    Return True if the any "draw" cards can be played(on top of the current
    card provided), otherwise return False
    """
    return any(match_draw_card(card, current_card) for card in cards)


def get_score(cards):
    """ 
    Calculate the score of given cards
    :cards a list of cards
    Card is a dict object
    @return an int of score
    """
    total = 0
    for card in cards:
        score = 0
        try:
            score = int(card['card_type'])
        except ValueError:
            if "wild" in card['card_type']:
                score = 50
            else:
                score = 20
        total += score
    return total