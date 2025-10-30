from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
import os


class ChatRoom(models.Model):
    """
    Model representing a chat room.
    Can be either a group chat or a private chat between two users.
    """
    ROOM_TYPE_CHOICES = [
        ('group', _('Group Chat')),
        ('private', _('Private Chat')),
    ]

    name = models.CharField(_('room name'), max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    room_type = models.CharField(
        _('room type'),
        max_length=10,
        choices=ROOM_TYPE_CHOICES,
        default='group'
    )
    description = models.TextField(_('description'), blank=True)
    image = models.ImageField(
        upload_to='chat/rooms/',
        blank=True,
        null=True,
        help_text=_('Room image/icon')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_rooms'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='RoomMembership',
        related_name='chat_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('chat room')
        verbose_name_plural = _('chat rooms')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('chat:room', kwargs={'slug': self.slug})

    @property
    def member_count(self):
        """Return the number of members in the room."""
        return self.members.count()

    def add_member(self, user, role='member'):
        """Add a member to the room."""
        RoomMembership.objects.get_or_create(
            room=self,
            user=user,
            defaults={'role': role}
        )

    def remove_member(self, user):
        """Remove a member from the room."""
        RoomMembership.objects.filter(room=self, user=user).delete()


class RoomMembership(models.Model):
    """
    Through model for the many-to-many relationship between User and ChatRoom.
    Tracks additional information about room membership.
    """
    ROLE_CHOICES = [
        ('admin', _('Admin')),
        ('moderator', _('Moderator')),
        ('member', _('Member')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='room_memberships'
    )
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        _('role'),
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'room']
        ordering = ['-joined_at']
        verbose_name = _('room membership')
        verbose_name_plural = _('room memberships')

    def __str__(self):
        return f"{self.user.username} - {self.room.name} ({self.role})"


class Message(models.Model):
    """
    Model representing a chat message.
    Supports text, images, and file attachments.
    """
    MESSAGE_TYPE_CHOICES = [
        ('text', _('Text')),
        ('image', _('Image')),
        ('file', _('File')),
        ('system', _('System')),
    ]

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages'
    )
    message_type = models.CharField(
        _('message type'),
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    content = models.TextField(_('content'), blank=True)
    image = models.ImageField(
        upload_to='chat/images/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    file = models.FileField(
        upload_to='chat/files/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'zip', 'rar'])]
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        sender_name = self.sender.username if self.sender else 'System'
        return f"{sender_name} in {self.room.name}: {self.content[:50]}"

    @property
    def file_name(self):
        """Return the filename of the attached file."""
        if self.file:
            return os.path.basename(self.file.name)
        elif self.image:
            return os.path.basename(self.image.name)
        return None

    @property
    def file_size(self):
        """Return the size of the attached file in bytes."""
        if self.file and self.file.size:
            return self.file.size
        elif self.image and self.image.size:
            return self.image.size
        return 0


class MessageRead(models.Model):
    """
    Model to track which messages have been read by which users.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_receipts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='read_messages'
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']
        ordering = ['-read_at']
        verbose_name = _('message read')
        verbose_name_plural = _('messages read')

    def __str__(self):
        return f"{self.user.username} read {self.message.id}"

