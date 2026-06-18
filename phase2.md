Phase 2 — Servers

What is a Server in our app?

A Server is like a community/group.
Example → "Django Developers" server

Every server has:
→ a name
→ an owner (user who created it)
→ an icon/image
→ members (users who joined)
→ channels (text/voice rooms inside it)
→ invite code (to join the server)

What APIs we need:

API 1 → Create Server
API 2 → Get Server Details
API 3 → Update Server (owner only)
API 4 → Delete Server (owner only)
API 5 → Join Server (via invite code)
API 6 → Leave Server
API 7 → List My Servers
API 8 → List Server Members

② Database Design — ALGORITHM

Tables needed:

Server Table
────────────────────────────────
id
name
description
icon          → server image
invite_code   → unique random code to join
owner         → FK to User
created_at

ServerMember Table
────────────────────────────────
id
server        → FK to Server
user          → FK to User
role          → owner/admin/moderator/member
joined_at

WHY TWO TABLES:
Server → stores server info
ServerMember → stores who is in which server with what role
One user can be in many servers
One server can have many users
This is a Many-to-Many relationship with extra data (role)


When a related object is deleted, on_delete tells Django what to do:

CASCADE → delete this object too (if user deleted → delete their servers)

SET_NULL → set field to NULL (keep server but remove owner reference)

PROTECT → prevent deletion if related objects exist

Instead of using sequential IDs (1, 2, 3) for invite codes, we use UUID (Universally Unique Identifier) — a random 32 character string like a3f8c2d1.... WHY → sequential invite codes are guessable. UUID is practically impossible to guess.

New Concept — settings.AUTH_USER_MODEL

Instead of importing User directly we use settings.AUTH_USER_MODEL. WHY → if someone changes the custom user model later, this reference updates automatically. Importing User directly can cause circular import errors in Django.

 New Concept — related_name

related_name lets you access related objects in reverse. owner = ForeignKey(User, related_name='owned_servers') means you can do user.owned_servers.all() to get all servers owned by a user. Without related_name Django auto-generates an ugly name.

⚠️ New Concept — unique_together

unique_together = ['server', 'user'] means the combination of server + user must be unique. A user cannot join the same server twice. Django enforces this at database level.


Create Server:
→ user sends name, description, icon
→ create server
→ automatically add creator as Owner in ServerMember
→ return server data

Join Server:
→ user sends invite_code
→ find server with that code
→ check user not already a member
→ add user as Member
→ return server data

Leave Server:
→ user sends request
→ check user is not owner (owner cannot leave)
→ remove user from ServerMember
→ return success

List My Servers:
→ find all ServerMember rows where user = request.user
→ return all those servers

