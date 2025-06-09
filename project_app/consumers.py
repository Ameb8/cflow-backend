from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
import docker
from asgiref.sync import sync_to_async
from .models import Project

class ExecConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['project_id']
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        self.docker_client = docker.from_env()

    async def disconnect(self, close_code):
        # Called when the socket closes
        pass

    async def receive(self, text_data):
        # Receive message from WebSocket
        data = json.loads(text_data)
        message = data.get('message', '')

        # Echo message back to client
        await self.send(text_data=json.dumps({
            'message': message
        }))
