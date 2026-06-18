What is a Channel?

A Channel lives INSIDE a server.
Think of it like rooms inside a building.

Server = Building
Channel = Room inside that building

Types:
→ Text Channel  → send/read messages
→ Voice Channel → voice calls
→ Video Channel → video calls

What APIs we need:

API 1 → Create Channel (admin/owner only)
API 2 → List Channels in a Server
API 3 → Get Channel Detail
API 4 → Update Channel (admin/owner only)
API 5 → Delete Channel (admin/owner only)

② Database Design

Channel Table
────────────────────────────────
id
name          → #general, #announcements
description   → optional channel description
channel_type  → text/voice/video
server        → FK to Server
created_by    → FK to User
is_private    → True/False
               private = only certain roles can see
created_at
updated_at

WHY is_private:
→ #admin-only channel → is_private=True
→ only admin/owner can see it
→ members cannot even see it exists

Create Channel:
→ only Owner or Admin can create
→ check user's role in server
→ create channel inside that server

List Channels:
→ user must be server member
→ if channel is_private=True
  → only show to owner and admin
→ return all visible channels

Update/Delete Channel:
→ only Owner or Admin can do this

Permission Check Algorithm:
→ get user's ServerMember record
→ check role is owner or admin
→ if not → return 403 Forbidden

New Concept — Reusable Permission Function

Instead of writing the same permission check in every view, we create ONE function that checks if a user is admin/owner in a server. We reuse it everywhere. This follows the DRY principle — Don't Repeat Yourself. You already know decorators — we will use one here too.

Step 2 — Create Permission Helper

⚠️ New Concept — Helper Function

A helper function is a reusable function that does one specific thing. We put it in a separate file called permissions.py. Any view that needs to check roles imports this function. Clean, reusable, easy to update in one place.




eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzgxNTc2OTQ3LCJpYXQiOjE3ODE1NzMzNDcsImp0aSI6ImY2ODMzYzFmY2RlZDQxNjNhNmFjZWE0MGNiNGNmYTIzIiwidXNlcl9pZCI6MX0.JMMyt2h3zSKkpagF_5w7wtsz-noLAenlCFrrBl75wjA

"id": 1