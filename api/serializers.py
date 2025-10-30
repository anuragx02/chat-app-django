from rest_framework import serializers
from accounts.models import User
from chat.models import ChatRoom, RoomMembership, Message, MessageRead


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'full_name', 'bio', 'avatar', 'is_online', 'last_seen', 'created_at']
        read_only_fields = ['id', 'is_online', 'last_seen', 'created_at']


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representations."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'is_online']


class RoomMembershipSerializer(serializers.ModelSerializer):
    """Serializer for RoomMembership model."""
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = RoomMembership
        fields = ['user', 'role', 'joined_at', 'is_muted', 'last_read_at']


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for ChatRoom model."""
    created_by = UserMinimalSerializer(read_only=True)
    members = UserMinimalSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    memberships = RoomMembershipSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'slug', 'room_type', 'description', 'image',
                  'created_by', 'members', 'member_count', 'memberships',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ChatRoom."""
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ChatRoom
        fields = ['name', 'room_type', 'description', 'image', 'member_ids']

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        user = self.context['request'].user
        
        # Create the room
        room = ChatRoom.objects.create(
            created_by=user,
            **validated_data
        )
        
        # Add creator as admin
        room.add_member(user, role='admin')
        
        # Add other members
        for member_id in member_ids:
            try:
                member = User.objects.get(id=member_id)
                room.add_member(member, role='member')
            except User.DoesNotExist:
                pass
        
        return room


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    sender = UserMinimalSerializer(read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        required=False,
        allow_null=True
    )
    file_name = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'message_type', 'content',
                  'image', 'file', 'file_name', 'file_size', 'reply_to',
                  'is_edited', 'edited_at', 'created_at']
        read_only_fields = ['id', 'sender', 'is_edited', 'edited_at', 'created_at']

    def validate(self, data):
        """Validate message data based on type."""
        message_type = data.get('message_type', 'text')
        
        if message_type == 'text' and not data.get('content'):
            raise serializers.ValidationError("Text messages must have content.")
        elif message_type == 'image' and not data.get('image'):
            raise serializers.ValidationError("Image messages must have an image.")
        elif message_type == 'file' and not data.get('file'):
            raise serializers.ValidationError("File messages must have a file.")
        
        return data


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages with file uploads."""
    
    class Meta:
        model = Message
        fields = ['room', 'message_type', 'content', 'image', 'file', 'reply_to']

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class MessageReadSerializer(serializers.ModelSerializer):
    """Serializer for MessageRead model."""
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = MessageRead
        fields = ['message', 'user', 'read_at']
        read_only_fields = ['user', 'read_at']
