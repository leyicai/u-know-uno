# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from unoGame.models import Game, Player, Card, GameRecord


class CardAdmin(admin.ModelAdmin):
    #   search_fields = ["game", "color",
                #    "in_use_by", "brand", "model", "type_number", "mac_address"]
    list_display = ("id", "game", "color", "card_type",
                    "is_on_deck", "is_current_card", "owner")

class PlayerInline(admin.TabularInline):
    model = Player

class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "game_players", "current_player", "is_joinable", "is_started", )
    inlines = [
        PlayerInline,
    ]

    def game_players(self, obj):
        return " ".join([player.user.username for player in obj.game_players.all()])
    
    def current_player(self, obj):
        return obj.get_current_player()
    
admin.site.register(Game, GameAdmin)
admin.site.register(Player)
admin.site.register(Card, CardAdmin)
admin.site.register(GameRecord)
