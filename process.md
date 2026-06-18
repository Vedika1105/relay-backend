Here is the exact order and WHY:

Step 1 → Create project folder (root of everything)
Step 2 → Create virtual environment INSIDE it
         WHY: isolates your project's packages from system Python
              so two projects never conflict with each other

Step 3 → Activate virtual environment
         WHY: every pip install after this goes ONLY into this project

Step 4 → Initialize Git
         WHY: do this AFTER venv so .gitignore can exclude venv folder

Step 5 → Create .gitignore
         WHY: before first commit so no junk files ever enter git history

Step 6 → Create folder structure
         WHY: clean structure = easy to scale, easy to explain in interview

Step 7 → Install packages in layers (base → dev → prod)
         WHY: not all packages are needed in production
              dev packages (like debugger) should never go to live server

Step 8 → Create versioned requirements files
         WHY: anyone (or any server) can recreate exact same environment
              with one command


NEW CONCEPT ALERT

⚠️ New Concept: Requirements File Splitting (base / dev / prod)
Most beginners use one requirements.txt. Professionals split it into three files. base.txt has packages needed everywhere. dev.txt has tools only for your laptop (like debuggers). prod.txt has tools only for the live server (like gunicorn). Each file "inherits" from base using -r base.txt. This is a direct interview green flag.

HOW TO EXPLAIN IN INTERVIEW ???

"I split requirements into base, dev, and prod layers so that development tools like debuggers never accidentally get deployed to production. Anyone cloning the project can recreate the exact same environment using pip install -r requirements/dev.txt. I used python-decouple to keep all secrets out of the codebase in a .env file."


The 3 Levels of Roles


Level 1 → PLATFORM LEVEL    (across whole app)
Level 2 → SERVER LEVEL      (inside each server)
Level 3 → CHANNEL LEVEL     (inside each channel)

These roles exist across the ENTIRE application

SUPERADMIN
──────────
→ You (the developer/owner of the platform)
→ Can delete any server, ban any user, see everything
→ Only 1 exists — you

Level 1 — Platform Level Roles

These roles exist across the ENTIRE application

REGULAR USER
────────────
→ Every person who registers on your platform
→ Can create servers, join servers, send messages
→ Default role when someone signs up

Every SERVER has its own role system
These roles only apply INSIDE that specific server

Level 2 — Server Level Roles
Every SERVER has its own role system
These roles only apply INSIDE that specific server

SERVER OWNER
────────────
→ Person who created that server
→ Has ALL permissions inside their server
→ Cannot be kicked or banned from own server
→ Can delete the entire server
→ Can transfer ownership to someone else

ADMIN
─────
→ Appointed by Server Owner
→ Can manage server settings
→ Can create/delete channels
→ Can assign roles to members
→ Can kick and ban members
→ Cannot ban Server Owner

MODERATOR
─────────
→ Appointed by Admin or Server Owner
→ Can delete any message in channels
→ Can kick members (not ban)
→ Can mute members temporarily
→ Cannot change server settings

MEMBER
──────
→ Default role when someone joins a server
→ Can read and send messages
→ Can join voice channels
→ Cannot manage anything

Level 3 — Channel Level Permissions
Inside each server, individual CHANNELS can have
their own permission overrides

Example:
  #announcements channel
  → Everyone can READ
  → Only Admin/Owner can WRITE

  #admin-only channel
  → Only Admins can see it
  → Members cannot even see it exists

  #general channel
  → Everyone can read and write

Permission                  SuperAdmin  Owner  Admin  Moderator  Member
────────────────────────────────────────────────────────────────────────
Delete platform users          ✅         ❌     ❌      ❌         ❌
Ban from platform              ✅         ❌     ❌      ❌         ❌
Create server                  ✅         ✅     ✅      ✅         ✅
Delete server                  ✅         ✅     ❌      ❌         ❌
Edit server settings           ✅         ✅     ✅      ❌         ❌
Create channels                ✅         ✅     ✅      ❌         ❌
Delete channels                ✅         ✅     ✅      ❌         ❌
Assign roles                   ✅         ✅     ✅      ❌         ❌
Ban from server                ✅         ✅     ✅      ❌         ❌
Kick from server               ✅         ✅     ✅      ✅         ❌
Delete any message             ✅         ✅     ✅      ✅         ❌
Mute members                   ✅         ✅     ✅      ✅         ❌
Send messages                  ✅         ✅     ✅      ✅         ✅
Read messages                  ✅         ✅     ✅      ✅         ✅
Join voice channels            ✅         ✅     ✅      ✅         ✅
Edit own messages              ✅         ✅     ✅      ✅         ✅
Delete own messages            ✅         ✅     ✅      ✅         ✅

How Roles Are Distributed

PLATFORM LEVEL
──────────────
User registers
→ automatically gets "Regular User" role
→ no manual assignment needed

SERVER LEVEL
────────────
User creates a server
→ automatically becomes "Server Owner" of that server

User joins a server
→ automatically gets "Member" role in that server

Server Owner promotes someone
→ Owner assigns "Admin" role manually

Admin promotes someone
→ Admin assigns "Moderator" role manually

CHANNEL LEVEL
─────────────
Admin/Owner creates a channel
→ sets permission overrides per role
→ example → make channel read-only for Members

How This Translates to Database

Tables we will create:

users table             → stores all platform users
servers table           → stores all servers
server_members table    → links users to servers + stores their role
channels table          → stores channels inside servers
channel_permissions     → stores permission overrides per channel per role

Interview Answer
"I designed a 3-level role system. Platform level handles app-wide roles like superadmin. Server level handles roles like owner, admin, moderator, member — each server has its own role assignments. Channel level allows permission overrides per channel. Roles are automatically assigned on registration and server creation, manually assigned by higher roles after that."

Let's Build — Starting With users App

What we are building right now:
  A Custom User Model — the foundation of everything

Why Custom and not Django's default?
  Django's default User has:
  → username, email, password, first_name, last_name
  
  Our app needs extra:
  → avatar (profile picture)
  → bio (about me)
  → status (online, offline, idle, do not disturb)
  → display_name (like Discord's nickname)

Step 1 → Create users app inside apps/ folder
Step 2 → Register app in settings.py
Step 3 → Build Custom User Model
Step 4 → Tell Django to use our model instead of default
Step 5 → Create and apply migrations
Step 6 → Verify in pgAdmin — new table appears

New Concept — Custom User Model

Django has a built-in User model. But it allows you to replace it completely with your own by extending AbstractUser. AbstractUser gives you everything Django's default user has PLUS lets you add your own fields on top. This MUST be done before your first app migration — changing it later is very painful and can break your database.

AbstractUser       → gives you EVERYTHING default user has
                     username, email, password, is_active etc
                     you just ADD extra fields on top
                     → WE USE THIS ✅ simpler

AbstractBaseUser   → gives you ONLY password and login logic
                     you build everything else from scratch
                     → too complex for now, used for very custom auth



What is an API and why do we need it?

Right now our Django app only serves HTML pages
through the admin panel.

But our Discord-like app needs:
  → Mobile app talking to backend
  → Frontend (React/Vue) talking to backend
  → WebSocket connections later

All of these communicate through APIs not HTML pages.

REST API works like this:
  Frontend sends REQUEST  → POST /api/users/register/
  Backend processes it    → creates user in database
  Backend sends RESPONSE  → {"id": 1, "username": "ayush"}

Django REST Framework (DRF) gives us tools to
build these APIs cleanly and efficiently.

?//////////   We need 3 APIs for users:

API 1 → Registration (signup)
─────────────────────────────
Request  → POST /api/users/register/
Input    → username, email, password
Process  → validate data → create user → return user data
Output   → {"id": 1, "username": "ayush", "email": "ayush@gmail.com"}
Auth     → no auth required (anyone can register)

API 2 → Login
──────────────
Request  → POST /api/users/login/
Input    → email, password
Process  → verify credentials → generate JWT tokens
Output   → {"access": "token...", "refresh": "token..."}
Auth     → no auth required (anyone can login)

API 3 → Profile (get and update)
─────────────────────────────────
Request  → GET  /api/users/profile/  (see profile)
           PUT  /api/users/profile/  (update profile)
Input    → JWT token in header
Process  → verify token → return/update user data
Output   → {"username": "ayush", "bio": "...", "status": "online"}
Auth     → MUST be logged in

For every API we need 3 things:

1. Serializer  → converts User model to/from JSON
                 like a translator between Python and JSON

2. View        → handles the request and returns response
                 the actual logic lives here

3. URL         → maps the endpoint to the view
                 /api/users/register/ → RegisterView


⚠️ New Concept — Serializer


In Django REST Framework, a Serializer is like a translator. Your database has Python objects (User model instances). The API needs JSON. A Serializer converts Python objects → JSON (called serialization) and JSON → Python objects (called deserialization). It also validates incoming data — checks if email is valid format, if password is strong enough etc.

For Login API We Need JWT

⚠️ New Concept — JWT (JSON Web Token)

When user logs in we cannot keep them logged in with
sessions (that is for HTML apps).

1. Simple JWT


What it does:
→ ONLY handles JWT token generation and verification
→ User logs in → gives access + refresh tokens
→ That's it — nothing else

What it does NOT do:
→ No Google/GitHub login
→ No email verification
→ No password reset
→ Just tokens

2. django-allauth

What it does:
→ Complete authentication system
→ Email/password registration and login
→ Email verification (sends confirmation email)
→ Password reset via email
→ Social login → Google, GitHub, Discord login
→ Works with DRF when combined with dj-rest-auth

What it does NOT do:
→ Does not generate JWT tokens alone
→ Needs Simple JWT alongside for token auth

Your Discord-like app needs:
→ Email + password registration    ✅
→ Email verification               ✅ (professional touch)
→ Password reset                   ✅ (basic requirement)
→ JWT tokens for API auth          ✅
→ Google/Discord social login      ✅ (nice to have)

Use BOTH together:

django-allauth   → handles all registration, login,
                   email verification, password reset
                   social login (Google, Discord)

Simple JWT       → handles JWT token generation
                   so APIs stay stateless

This combo is used by most Django startups in India.
You OWN all the code.
You can explain every part in interviews.
No external service dependency.

"I used django-allauth for complete authentication — registration, email verification, password reset, and social login. I combined it with Simple JWT so all my APIs use stateless token-based authentication. This way I own all the auth logic, nothing depends on external paid services, and the whole flow is fully customizable."

django-allauth is a complete authentication package. It handles EVERYTHING related to auth — registration, login, logout, email verification, password reset, social login. It creates its own database tables to store email addresses, social account connections etc. It works alongside Simple JWT — allauth handles the auth LOGIC, JWT handles the TOKENS.

Profile API (GET):
  Step 1 → User sends GET request to /api/users/profile/
  Step 2 → Django checks Authorization header for JWT token
  Step 3 → Token valid → find user from token's user_id
  Step 4 → Return user's profile data as JSON

Profile API (PUT):
  Step 1 → User sends PUT request to /api/users/profile/
           with fields they want to update
  Step 2 → Django verifies JWT token
  Step 3 → Validate incoming data
  Step 4 → Update only fields that were sent
  Step 5 → Return updated profile data

Logout API (POST):
  Step 1 → User sends POST request to /api/users/logout/
           with their refresh token
  Step 2 → Django verifies access token
  Step 3 → Blacklist the refresh token
           WHY → so it cannot be used to generate
                 new access tokens anymore
  Step 4 → Return success message

⚠️ New Concept — Token Blacklisting

When a user logs out we cannot "delete" JWT tokens — they are stateless and live on the client side. Instead we blacklist the refresh token — add it to a blocked list in database. When someone tries to use a blacklisted refresh token → Django rejects it. Simple JWT has a built-in blacklist app for this.

Phase 1 Summary — What You Built

✅ Custom User Model
   → display_name, bio, avatar, status
   → unique email, TextChoices for status

✅ PostgreSQL connected

✅ Django Admin with secret URL

✅ Registration API
   → regex username validation
   → password strength validation
   → password hashing

✅ Login API
   → JWT access + refresh tokens
   → status updated to online

✅ Profile API
   → GET and PUT
   → partial updates

✅ Logout API
   → token blacklisting
   → status updated to offline

✅ Change Password API
   → old password verification
   → new password validation



