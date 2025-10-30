import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message, RoomMembership


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat messages.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f'chat_{self.room_slug}'
        self.user = self.scope['user']

        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Check if user is a member of the room
        is_member = await self.is_room_member()
        if not is_member:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Update user online status
        await self.update_user_status(True)

        # Send user joined notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'username': self.user.username,
                'status': 'joined'
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Update user online status
        await self.update_user_status(False)

        # Send user left notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'username': self.user.username,
                'status': 'left'
            }
        )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'text')
            content = data.get('content', '')

            if message_type == 'text' and content.strip():
                # Save message to database
                message = await self.save_message(
                    message_type='text',
                    content=content
                )

                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'sender': self.user.username,
                            'sender_id': self.user.id,
                            'content': content,
                            'message_type': 'text',
                            'created_at': message.created_at.isoformat(),
                        }
                    }
                )
            elif message_type == 'typing':
                # Handle typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'username': self.user.username,
                        'is_typing': data.get('is_typing', False)
                    }
                )
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_status(self, event):
        """Send user status update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'username': event['username'],
            'status': event['status']
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator back to the sender
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    @database_sync_to_async
    def is_room_member(self):
        """Check if the user is a member of the room."""
        try:
            room = ChatRoom.objects.get(slug=self.room_slug)
            return RoomMembership.objects.filter(
                room=room,
                user=self.user
            ).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message_type, content):
        """Save a message to the database."""
        room = ChatRoom.objects.get(slug=self.room_slug)
        message = Message.objects.create(
            room=room,
            sender=self.user,
            message_type=message_type,
            content=content
        )
        return message

    @database_sync_to_async
    def update_user_status(self, is_online):
        """Update user online status."""
        self.user.is_online = is_online
        self.user.last_seen = timezone.now()
        self.user.save(update_fields=['is_online', 'last_seen'])
