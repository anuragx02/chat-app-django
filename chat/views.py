from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Q, Max
from .models import ChatRoom, RoomMembership, Message
from accounts.models import User


@login_required
def lobby_view(request):
    """Display the chat lobby with list of rooms."""
    # Get rooms where user is a member
    user_rooms = ChatRoom.objects.filter(
        members=request.user
    ).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time', '-updated_at')
    
    # Get available users for private chat
    available_users = User.objects.exclude(
        id=request.user.id
    ).order_by('username')[:20]
    
    context = {
        'rooms': user_rooms,
        'available_users': available_users,
    }
    return render(request, 'chat/lobby.html', context)


@login_required
def room_view(request, slug):
    """Display a specific chat room."""
    room = get_object_or_404(ChatRoom, slug=slug)
    
    # Check if user is a member
    membership = RoomMembership.objects.filter(
        room=room,
        user=request.user
    ).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this room.')
        return redirect('chat:lobby')
    
    # Get recent messages
    messages_list = Message.objects.filter(
        room=room
    ).select_related('sender').order_by('-created_at')[:50]
    
    # Reverse to show oldest first
    messages_list = list(reversed(messages_list))
    
    # Get room members
    memberships = RoomMembership.objects.filter(
        room=room
    ).select_related('user')
    
    context = {
        'room': room,
        'messages': messages_list,
        'memberships': memberships,
        'user_membership': membership,
    }
    return render(request, 'chat/room.html', context)


@login_required
def create_room_view(request):
    """Create a new chat room."""
    if request.method == 'POST':
        name = request.POST.get('name')
        room_type = request.POST.get('room_type', 'group')
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, 'Room name is required.')
            return redirect('chat:create_room')
        
        # Create slug from name
        slug = slugify(name)
        
        # Ensure slug is unique
        original_slug = slug
        counter = 1
        while ChatRoom.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Create room
        room = ChatRoom.objects.create(
            name=name,
            slug=slug,
            room_type=room_type,
            description=description,
            created_by=request.user
        )
        
        # Add creator as admin
        room.add_member(request.user, role='admin')
        
        # Add selected members if any
        member_ids = request.POST.getlist('members')
        for member_id in member_ids:
            try:
                user = User.objects.get(id=member_id)
                room.add_member(user, role='member')
            except User.DoesNotExist:
                pass
        
        messages.success(request, f'Room "{name}" created successfully!')
        return redirect('chat:room', slug=slug)
    
    # Get available users for adding to room
    available_users = User.objects.exclude(
        id=request.user.id
    ).order_by('username')
    
    context = {
        'available_users': available_users,
    }
    return render(request, 'chat/create_room.html', context)


@login_required
def private_chat_view(request, user_id):
    """Create or get a private chat with another user."""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        messages.error(request, 'You cannot create a private chat with yourself.')
        return redirect('chat:lobby')
    
    # Check if private room already exists between these users
    private_rooms = ChatRoom.objects.filter(
        room_type='private',
        members=request.user
    ).filter(
        members=other_user
    )
    
    if private_rooms.exists():
        room = private_rooms.first()
    else:
        # Create new private room
        room_name = f"{request.user.username} & {other_user.username}"
        slug = slugify(f"private-{request.user.id}-{other_user.id}")
        
        room = ChatRoom.objects.create(
            name=room_name,
            slug=slug,
            room_type='private',
            created_by=request.user
        )
        
        # Add both users as members
        room.add_member(request.user, role='admin')
        room.add_member(other_user, role='admin')
    
    return redirect('chat:room', slug=room.slug)

