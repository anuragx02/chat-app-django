from django.contrib import admin
from django.utils.html import format_html
from .models import ChatRoom, RoomMembership, Message, MessageRead


class RoomMembershipInline(admin.TabularInline):
    """Inline admin for room memberships."""
    model = RoomMembership
    extra = 1
    fields = ['user', 'role', 'joined_at', 'is_muted']
    readonly_fields = ['joined_at']


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """Admin configuration for ChatRoom model."""
    
    list_display = ['name', 'room_type', 'member_count', 'created_by', 'created_at']
    list_filter = ['room_type', 'created_at']
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-created_at']
    inlines = [RoomMembershipInline]
    
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'room_type')}),
        ('Details', {'fields': ('description', 'image')}),
        ('Management', {'fields': ('created_by',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def member_count(self, obj):
        """Display member count."""
        return obj.member_count
    member_count.short_description = 'Members'


@admin.register(RoomMembership)
class RoomMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for RoomMembership model."""
    
    list_display = ['user', 'room', 'role', 'joined_at', 'is_muted']
    list_filter = ['role', 'is_muted', 'joined_at']
    search_fields = ['user__username', 'room__name']
    ordering = ['-joined_at']
    
    fieldsets = (
        (None, {'fields': ('user', 'room', 'role')}),
        ('Settings', {'fields': ('is_muted', 'last_read_at')}),
        ('Timestamps', {'fields': ('joined_at',)}),
    )
    
    readonly_fields = ['joined_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin configuration for Message model."""
    
    list_display = ['id', 'sender', 'room', 'message_type', 'content_preview', 'created_at', 'is_edited']
    list_filter = ['message_type', 'is_edited', 'created_at', 'room']
    search_fields = ['content', 'sender__username', 'room__name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {'fields': ('room', 'sender', 'message_type')}),
        ('Content', {'fields': ('content', 'image', 'file', 'reply_to')}),
        ('Edit Info', {'fields': ('is_edited', 'edited_at')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
    
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        """Display a preview of the message content."""
        if obj.message_type == 'text':
            return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        elif obj.message_type == 'image':
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url) if obj.image else 'No image'
        elif obj.message_type == 'file':
            return obj.file_name or 'No file'
        return 'System message'
    content_preview.short_description = 'Content'


@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    """Admin configuration for MessageRead model."""
    
    list_display = ['user', 'message', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'message__content']
    ordering = ['-read_at']
    date_hierarchy = 'read_at'
    
    fieldsets = (
        (None, {'fields': ('message', 'user')}),
        ('Timestamps', {'fields': ('read_at',)}),
    )
    
    readonly_fields = ['read_at']

