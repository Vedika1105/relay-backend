How Real-time Messaging Works:

Normal HTTP (what we used till now):
  Client sends request → Server responds → connection closes
  Problem → server cannot send message TO client without request not suitable for chat

WebSocket (what we need now):
  Client connects → connection stays OPEN permanently
  Server can push messages to client anytime
  Client can send messages to server anytime
  Perfect for real-time chat

Flow:
  User A opens chat in channel
  → WebSocket connection opens
  → connection stays alive

  User A types message and sends
  → message goes through WebSocket
  → Django Channels receives it
  → saves to database
  → broadcasts to ALL users in same channel
  → User B and C receive message instantly
  → no page refresh needed


Two new packages:

1. channels     → adds WebSocket support to Django
                  Django alone only handles HTTP
                  channels adds WebSocket on top

2. channels-redis → connects Django Channels to Redis
                    Redis acts as message broker
                    broadcasts messages between connections

3. Redis itself → must be running on your machine
                  as a separate service

⚠️ New Concept — Django Channels

Django by default is synchronous — it handles one request at a time. Django Channels extends Django to handle asynchronous connections like WebSockets. It introduces a concept called Consumer which is like a Django View but for WebSocket connections instead of HTTP requests.

⚠️ New Concept — Consumer

A Consumer is Django Channels equivalent of a View. But instead of handling one request and closing, a Consumer handles a persistent WebSocket connection. It has methods like connect(), disconnect(), and receive() — called automatically when those events happen.

⚠️ New Concept — Channel Layer

A Channel Layer is a system that allows different WebSocket connections to communicate with each other. When User A sends a message, the Channel Layer broadcasts it to ALL other connections in the same room. Redis is the backend that powers this layer.

⚠️ New Concept — Async/Await

Django Channels uses async/await — a Python feature for writing asynchronous code. Instead of def connect() you write async def connect(). Instead of calling functions normally you use await. This allows handling thousands of WebSocket connections simultaneously without blocking.


Step 2 — Update config/asgi.py

⚠️ New Concept — ASGI

Django normally uses WSGI (Web Server Gateway Interface) which only handles HTTP. ASGI (Asynchronous Server Gateway Interface) handles both HTTP AND WebSockets. Django Channels replaces WSGI with ASGI to support real-time connections.

How WebSocket Chat Works:

Step 1 → User opens channel in browser
         Frontend connects to WebSocket:
         ws://localhost:8000/ws/chat/<channel_id>/

Step 2 → Consumer's connect() method fires
         → verify user is authenticated
         → verify user is member of server
         → join the channel group in Redis
         → accept connection

Step 3 → User sends message
         → Consumer's receive() method fires
         → save message to database
         → broadcast to ALL users in channel group

Step 4 → All connected users receive message instantly
         → no page refresh needed

Step 5 → User closes browser/leaves channel
         → Consumer's disconnect() method fires
         → remove from channel group

⚠️ New Concept — AsyncWebsocketConsumer

A Consumer is like a View but for WebSockets. AsyncWebsocketConsumer has 3 main methods:

connect() → called when WebSocket connection opens

disconnect() → called when connection closes

receive() → called when message arrives from client

All methods use async/await because they handle many connections simultaneously.

Step 2 — Create apps/messaging/routing.py

⚠️ New Concept — routing.py

Just like urls.py maps HTTP URLs to views, routing.py maps WebSocket URLs to consumers. Same concept, different protocol.


Step 5 — Install daphne (ASGI Server)

⚠️ New Concept — Daphne

Django's built-in runserver only handles HTTP. Daphne is an ASGI server that handles both HTTP and WebSockets. We need it to run our WebSocket consumer locally.

Message History API:
→ User opens a channel
→ Frontend needs to load past messages
→ WebSocket only handles LIVE messages
→ REST API handles HISTORY

GET /api/messages/<channel_id>/
→ check user is member of server
→ fetch last 50 messages (newest last)
→ return as JSON list

WHY 50 messages:
→ loading all messages at once = slow
→ 50 is enough for initial load
→ user scrolls up → load more (pagination)

⚠️ New Concept — Pagination

Loading ALL messages at once is bad for performance. Pagination splits results into pages — load 50 messages first, then load next 50 when user scrolls up. We use DRF's built-in PageNumberPagination for this.


Fix — JWT WebSocket Middleware

⚠️ New Concept — WebSocket Middleware

For REST APIs, JWT token comes in Authorization header. For WebSockets, token is passed as a URL query parameter because WebSocket connections cannot send custom headers easily. We create middleware that reads token from URL and authenticates the user before consumer runs.