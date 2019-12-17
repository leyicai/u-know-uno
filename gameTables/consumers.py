""" Websocket Function for Public Chatting in Game Lobby """
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    CONNECTED_USERS = []
    def connect(self):
        self.room_group_name = 'public_chat'

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        ChatConsumer.CONNECTED_USERS.append(self)
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        if self in ChatConsumer.CONNECTED_USERS:
            ChatConsumer.CONNECTED_USERS.remove(self)

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # print(self.scope['user'].username, text_data_json)

        if 'message' in text_data:
            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': text_data_json['message'],
                    'username': self.scope["user"].username
                }
            )
        elif 'new' in text_data:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'reload_message',
                    'username': self.scope['user'].username,
                }
            )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        # print(event)

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'username': event['username']
        }))
    
    def reload_message(self, event):
        print(self.scope['user'].username, event)
        if event['username'] != self.scope['user'].username:
            self.send(text_data=json.dumps({
                'type': 'reload_message'
            }))
        # for user in ChatConsumer.CONNECTED_USERS:
        #     user.send(text_data=json.dumps({'type': 'reload_message'}))