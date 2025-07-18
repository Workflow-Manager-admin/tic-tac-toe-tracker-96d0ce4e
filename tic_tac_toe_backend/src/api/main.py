from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError

from .db import get_session_factory, User
from .schemas import UserCreate, UserLogin, UserOut, Token
from .auth import get_password_hash, verify_password, create_access_token
from sqlalchemy.orm import Session

from .game import router as game_router

app = FastAPI(
    title="Tic Tac Toe API",
    version="1.0.0",
    description="API backend for Tic Tac Toe game with user management, session auth, game logic, and match history.\n\n"
                "## Authentication\n"
                "Authenticate using Bearer JWT token. Protected endpoints require:\n"
                "  - `Authorization: Bearer <token>`\n\n"
                "## Game Endpoints\n"
                "- `/game/start`: Start a new game\n"
                "- `/game/{game_id}/move`: Make a move in a game\n"
                "- `/game/{game_id}`: Get game state\n"
                "- `/game/history`: Get your match history\n",
    openapi_tags=[
        {"name": "auth", "description": "User registration, login, JWT auth"},
        {"name": "system", "description": "System and health check endpoints"},
        {"name": "game", "description": "Tic Tac Toe game logic endpoints"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Game router
app.include_router(game_router)

@app.get("/", tags=["system"], summary="Health Check")
def health_check():
    """Basic health check to verify API is running."""
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Register new user",
    responses={
        201: {"description": "User registered successfully."},
        400: {"description": "Username or email already exists."}
    }
)
def register_user(user: UserCreate = Body(...), db: Session = Depends(get_session_factory())):
    """
    Register a new Tic Tac Toe user account.

    - **username**: unique username (case-insensitive)
    - **email**: user email
    - **password**: desired password
    """
    username = user.username.lower()
    email = user.email.lower()
    password_hash = get_password_hash(user.password)

    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists.",
        )

    return UserOut.from_orm(new_user)

# PUBLIC_INTERFACE
@app.post(
    "/login",
    response_model=Token,
    tags=["auth"],
    summary="User login",
    responses={
        200: {"description": "Successful login returns JWT token."},
        401: {"description": "Incorrect username or password."}
    },
)
def login_user(login: UserLogin = Body(...), db: Session = Depends(get_session_factory())):
    """
    Authenticate user and return JWT bearer token.

    - **username**: Your username (case-insensitive)
    - **password**: Your password
    """
    user = db.query(User).filter(User.username == login.username.lower()).first()
    if not user or not verify_password(login.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )
    # Issue JWT
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

