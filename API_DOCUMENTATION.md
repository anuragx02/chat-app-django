# API Documentation

## Authentication

The API supports three authentication methods:
1. Session Authentication (for browser-based clients)
2. Token Authentication (for mobile/desktop apps)
3. JWT Authentication (for modern SPAs)

### Obtaining JWT Token

**POST** `/api/token/`

Request body:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refreshing Token

**POST** `/api/token/refresh/`

Request body:
```json
{
  "refresh": "your_refresh_token"
}
```

## Users Endpoints

### List Users
**GET** `/api/users/`

Query parameters:
- `search` - Search by username, name, or email
- `exclude_self` - Set to `true` to exclude current user

### Get Current User
**GET** `/api/users/me/`

### Get User Detail
**GET** `/api/users/{id}/`

### Update Profile
**PATCH** `/api/users/{id}/update_profile/`

Request body:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Software Developer",
  "avatar": "<file>"
}
```

## Chat Rooms Endpoints

### List User's Rooms
**GET** `/api/rooms/`

Query parameters:
- `search` - Search by room name or description

### Create Room
**POST** `/api/rooms/`

Request body:
```json
{
  "name": "My Chat Room",
  "room_type": "group",
  "description": "A chat room for my team",
  "member_ids": [1, 2, 3]
}
```

### Get Room Detail
**GET** `/api/rooms/{id}/`

### Join Room
**POST** `/api/rooms/{id}/join/`

### Leave Room
**POST** `/api/rooms/{id}/leave/`

### Get Room Members
**GET** `/api/rooms/{id}/members/`

### Add Member to Room (Admin only)
**POST** `/api/rooms/{id}/add_member/`

Request body:
```json
{
  "user_id": 5
}
```

## Messages Endpoints

### List Messages
**GET** `/api/messages/`

Query parameters:
- `room_id` - Filter by room ID
- `search` - Search message content

### Send Message
**POST** `/api/messages/`

For text messages:
```json
{
  "room": 1,
  "message_type": "text",
  "content": "Hello, world!"
}
```

For image messages:
```json
{
  "room": 1,
  "message_type": "image",
  "image": "<file>"
}
```

For file messages:
```json
{
  "room": 1,
  "message_type": "file",
  "file": "<file>"
}
```

### Edit Message
**PATCH** `/api/messages/{id}/edit/`

Request body:
```json
{
  "content": "Updated message content"
}
```

### Mark Message as Read
**POST** `/api/messages/{id}/mark_read/`

## WebSocket Connection

Connect to WebSocket for real-time messaging:

```
ws://localhost:8000/ws/chat/{room_slug}/
```

### Message Format

Sending a text message:
```json
{
  "type": "text",
  "content": "Hello, everyone!"
}
```

Sending typing indicator:
```json
{
  "type": "typing",
  "is_typing": true
}
```

### Receiving Messages

Chat message:
```json
{
  "type": "chat_message",
  "message": {
    "id": 1,
    "sender": "john",
    "sender_id": 1,
    "content": "Hello!",
    "message_type": "text",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

User status:
```json
{
  "type": "user_status",
  "username": "john",
  "status": "joined"
}
```

Typing indicator:
```json
{
  "type": "typing_indicator",
  "username": "john",
  "is_typing": true
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "error": "Error message here"
}
```

or

```json
{
  "field_name": ["Error message for this field"]
}
```

## Rate Limiting

API endpoints may be rate limited. Rate limit information is included in response headers:
- `X-RateLimit-Limit` - Request limit per hour
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Time when limit resets (Unix timestamp)

## Pagination

List endpoints support pagination:

Query parameters:
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 50, max: 100)

Response includes:
```json
{
  "count": 150,
  "next": "http://api.example.com/users/?page=2",
  "previous": null,
  "results": [...]
}
```
