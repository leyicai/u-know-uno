from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # re_path(r'unoGame/startGame/$', consumers.GameConsumer),
    re_path(r'ws/chat/(?P<game_id>\d+)/$',
            consumers.GameChatConsumer, name="game_chat"),
    re_path(r'ws/(?P<game_id>\d+)/$',
            consumers.GameConsumer, name='in_game'),
]
