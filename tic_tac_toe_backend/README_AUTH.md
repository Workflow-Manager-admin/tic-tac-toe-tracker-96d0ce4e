# Tic Tac Toe Backend Auth Setup

## Required Environment Variables

You must add the following to your `.env` file **(project root)** before running the backend:

```
JWT_SECRET=your_super_secret_jwt_signing_key
```

Replace `your_super_secret_jwt_signing_key` with a long, random value. This is required for secure token authentication.

## Endpoints

- `POST /register` (username, email, password) — User registration.
- `POST /login` (username, password) — Returns JWT token on success.

Both endpoints are fully documented in /docs (OpenAPI).
