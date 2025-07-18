from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """User registration request schema."""
    username: str = Field(..., min_length=3, max_length=32, description="Unique username (case-insensitive)")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Account password, min 6 characters")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """User login request schema."""
    username: str = Field(..., min_length=3, max_length=32, description="Your username")
    password: str = Field(..., min_length=6, description="Your password")

# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """Public user info schema."""
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class Token(BaseModel):
    """JWT access token schema."""
    access_token: str = Field(..., description="JWT Bearer token")
    token_type: str = Field("bearer", description="Token type (always bearer)")

# ---- GAME LOGIC SCHEMAS ----

class StartGameRequest(BaseModel):
    """Request schema for starting a new game."""
    opponent_username: Optional[str] = Field(None, description="If vs player mode, provide opponent's username. If not provided, game is vs computer.")
    game_mode: str = Field("vs_player", description="Game mode: 'vs_player' or 'vs_computer'")

class StartGameResponse(BaseModel):
    """Response for starting a new game."""
    game_id: int
    status: str
    current_turn: str
    game_mode: str

class MoveRequest(BaseModel):
    """Request schema for making a move."""
    row: int = Field(..., ge=0, le=2, description="Row (0-2)")
    col: int = Field(..., ge=0, le=2, description="Col (0-2)")

class MoveResponse(BaseModel):
    """Response after a move is made."""
    board: List[List[Optional[str]]] = Field(..., description="3x3 board after the move")
    status: str
    winner: Optional[str] = Field(None, description="Username of the winner if game ended, else None")
    is_draw: bool = Field(..., description="Game ended in a draw?")

class GameStateResponse(BaseModel):
    """Response for getting game state."""
    game_id: int
    board: List[List[Optional[str]]]
    current_turn: str
    status: str
    moves: List["MoveEntry"]
    player_x: str
    player_o: Optional[str]
    winner: Optional[str]
    is_draw: bool

class MoveEntry(BaseModel):
    move_number: int
    player: str
    row: int
    col: int
    symbol: str
    moved_at: str

GameStateResponse.model_rebuild()

class HistoryEntry(BaseModel):
    game_id: int
    player_x: str
    player_o: Optional[str]
    result: str
    winner: Optional[str]
    finished_at: str

class GameHistoryResponse(BaseModel):
    """Response schema for /history endpoint."""
    games: List[HistoryEntry]
