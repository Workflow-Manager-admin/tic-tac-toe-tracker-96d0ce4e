# Tic Tac Toe Backend Auth & Game Setup

## Required Environment Variables

You must add the following to your `.env` file **(project root)** before running the backend:

```
JWT_SECRET=your_super_secret_jwt_signing_key
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_HOST=your_mysql_host
DB_PORT=your_mysql_port
DB_NAME=your_mysql_database
```

Replace `your_super_secret_jwt_signing_key` with a long, random value. This is required for secure token authentication.
Set `DB_*` values to match your deployed MySQL instance (see database container for details).

## Endpoints

- `POST /register` (username, email, password) — User registration.
- `POST /login` (username, password) — Returns JWT token on success.
- `POST /game/start` — Start a new game (protected, Bearer JWT required)
- `POST /game/{game_id}/move` — Make a move in a game (protected, Bearer JWT required)
- `GET /game/{game_id}` — Fetch current state of a game (protected)
- `GET /game/history` — Retrieve match/game history for a user (protected)

All endpoints are fully documented in /docs (OpenAPI).

**Dependencies:**
- FastAPI
- SQLAlchemy
- python-jose[cryptography]
- passlib[bcrypt]
- python-dotenv
- MySQL connector

No additional packages required for Tic Tac Toe logic.
