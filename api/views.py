from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import User
from chat.models import ChatRoom, Message, RoomMembership, MessageRead
from .serializers import (
    UserSerializer, ChatRoomSerializer, ChatRoomCreateSerializer,
    MessageSerializer, MessageCreateSerializer, RoomMembershipSerializer,
    MessageReadSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User operations."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']

    def get_queryset(self):
        """Filter users based on query params."""
        queryset = super().get_queryset()
        
        # Exclude current user if requested
        exclude_self = self.request.query_params.get('exclude_self', 'false')
        if exclude_self.lower() == 'true':
            queryset = queryset.exclude(id=self.request.user.id)
        
        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_profile(self, request, pk=None):
        """Update user profile."""
        user = self.get_object()
        
        # Ensure user can only update their own profile
        if user != request.user:
            return Response(
                {'error': 'You can only update your own profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChatRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for ChatRoom operations."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        """Get rooms that the user is a member of."""
        return ChatRoom.objects.filter(
            members=self.request.user
        ).distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a chat room."""
        room = self.get_object()
        user = request.user
        
        # Check if already a member
        if RoomMembership.objects.filter(room=room, user=user).exists():
            return Response(
                {'message': 'Already a member of this room.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user as member
        room.add_member(user, role='member')
        
        return Response(
            {'message': f'Successfully joined {room.name}'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a chat room."""
        room = self.get_object()
        user = request.user
        
        # Check if member
        membership = RoomMembership.objects.filter(room=room, user=user).first()
        if not membership:
            return Response(
                {'error': 'Not a member of this room.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow admin to leave if they're the only admin
        if membership.role == 'admin':
            admin_count = RoomMembership.objects.filter(
                room=room,
                role='admin'
            ).count()
            if admin_count == 1:
                return Response(
                    {'error': 'Cannot leave room as the only admin. Assign another admin first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Remove user from room
        room.remove_member(user)
        
        return Response(
            {'message': f'Successfully left {room.name}'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of a room."""
        room = self.get_object()
        memberships = RoomMembership.objects.filter(room=room)
        serializer = RoomMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the room (admin only)."""
        room = self.get_object()
        user = request.user
        
        # Check if user is admin
        membership = RoomMembership.objects.filter(room=room, user=user).first()
        if not membership or membership.role != 'admin':
            return Response(
                {'error': 'Only admins can add members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get user to add
        user_id = request.data.get('user_id')
        try:
            new_member = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add member
        room.add_member(new_member, role='member')
        
        return Response(
            {'message': f'{new_member.username} added to {room.name}'},
            status=status.HTTP_200_OK
        )


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for Message operations."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['content']

    def get_queryset(self):
        """Get messages for rooms the user is a member of."""
        user = self.request.user
        
        # Get room_id from query params
        room_id = self.request.query_params.get('room_id')
        
        queryset = Message.objects.filter(
            room__members=user
        ).select_related('sender', 'room', 'reply_to').order_by('created_at')
        
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request, *args, **kwargs):
        """Create a new message."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user is a member of the room
        room = serializer.validated_data['room']
        if not RoomMembership.objects.filter(room=room, user=request.user).exists():
            return Response(
                {'error': 'You must be a member of this room to send messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['patch'])
    def edit(self, request, pk=None):
        """Edit a message."""
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow editing text messages
        if message.message_type != 'text':
            return Response(
                {'error': 'Only text messages can be edited.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        content = request.data.get('content')
        if content:
            from django.utils import timezone
            message.content = content
            message.is_edited = True
            message.edited_at = timezone.now()
            message.save()
            
            serializer = self.get_serializer(message)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Content is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read."""
        message = self.get_object()
        user = request.user
        
        # Don't mark own messages as read
        if message.sender == user:
            return Response(
                {'message': 'Cannot mark own message as read.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or get read receipt
        read_receipt, created = MessageRead.objects.get_or_create(
            message=message,
            user=user
        )
        
        serializer = MessageReadSerializer(read_receipt)
        return Response(serializer.data)

