from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from typing import List, Optional

from .db import get_session_factory, User, Game, Move, MatchHistory
from .auth import get_current_user
from .schemas import (
    StartGameRequest,
    StartGameResponse,
    MoveRequest,
    MoveResponse,
    GameStateResponse,
    MoveEntry,
    GameHistoryResponse,
    HistoryEntry,
)

router = APIRouter(
    prefix="/game",
    tags=["game"],
)

def empty_board():
    """Returns an empty 3x3 tic-tac-toe board."""
    return [[None for _ in range(3)] for _ in range(3)]

def reconstruct_board(moves: List[Move]) -> List[List[Optional[str]]]:
    board = empty_board()
    for move in moves:
        board[move.row][move.col] = move.symbol
    return board

def check_winner(board):
    """Returns 'X', 'O', or None according to win/draw state."""
    lines = []
    # rows and cols
    for i in range(3):
        lines.append(board[i])  # row
        lines.append([board[0][i], board[1][i], board[2][i]])  # col
    # diagonals
    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])
    for line in lines:
        if line[0] and all(cell == line[0] for cell in line):
            return line[0]
    if all(cell is not None for row in board for cell in row):
        return "draw"
    return None

# PUBLIC_INTERFACE
@router.post(
    "/start",
    response_model=StartGameResponse,
    summary="Start a new Tic Tac Toe game",
    description="Create a new game. If opponent_username is provided and valid, starts a vs_player game. Otherwise, starts vs_computer.",
    status_code=201,
    responses={201: {"description": "Game created."}, 400: {"description": "Opponent invalid or unavailable."}},
)
def start_game(
    req: StartGameRequest = Body(...),
    db: Session = Depends(get_session_factory()),
    current_user: User = Depends(get_current_user)
):
    """Create a new Tic Tac Toe game with an opponent or computer (vs AI)."""
    if req.opponent_username and req.game_mode == "vs_player":
        opponent = db.query(User).filter(User.username == req.opponent_username.lower()).first()
        if not opponent or opponent.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or unavailable opponent."
            )
        player_o_id = opponent.id
        game_mode = "vs_player"
    else:
        player_o_id = None
        game_mode = "vs_computer"

    new_game = Game(
        player_x_id=current_user.id,
        player_o_id=player_o_id,
        status="in_progress" if player_o_id else "in_progress",
        current_turn="X",
        game_mode=game_mode
    )
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return StartGameResponse(
        game_id=new_game.id,
        status=new_game.status,
        current_turn=new_game.current_turn,
        game_mode=game_mode
    )

# PUBLIC_INTERFACE
@router.post(
    "/{game_id}/move",
    response_model=MoveResponse,
    summary="Make a move in a Tic Tac Toe game",
    description="Make a move as the authenticated player in a specified game.",
    status_code=200,
    responses={
        200: {"description": "Move accepted. Board updated."},
        400: {"description": "Invalid move or not this user's turn."},
        404: {"description": "Game not found."}
    }
)
def make_move(
    game_id: int = Path(..., description="ID of the game"),
    move: MoveRequest = Body(...),
    db: Session = Depends(get_session_factory()),
    current_user: User = Depends(get_current_user)
):
    """Make a move as X or O. Validates turn and move legality."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status not in ("in_progress",):
        raise HTTPException(status_code=400, detail="Game is not active")

    symbol = None
    if game.player_x_id == current_user.id:
        symbol = "X"
    elif game.player_o_id == current_user.id:
        symbol = "O"
    elif game.player_o_id is None and game.game_mode == "vs_computer":
        symbol = "X"
    else:
        raise HTTPException(status_code=400, detail="Player not part of this game.")

    # Check current turn
    if game.current_turn != symbol:
        raise HTTPException(status_code=400, detail="Not your turn.")

    # Collect all moves and build board
    moves = db.query(Move).filter(Move.game_id == game_id).order_by(Move.move_number).all()
    board = reconstruct_board(moves)
    if board[move.row][move.col] is not None:
        raise HTTPException(status_code=400, detail="Cell already occupied.")

    next_move_num = len(moves) + 1
    # Make move
    move_obj = Move(
        game_id=game_id,
        move_number=next_move_num,
        player_id=current_user.id,
        row=move.row,
        col=move.col,
        symbol=symbol
    )
    db.add(move_obj)
    board[move.row][move.col] = symbol

    # Check for win/draw after move
    winner_symbol = check_winner(board)
    winner_id = None
    is_draw = False
    status = "in_progress"
    if winner_symbol == "draw":
        status = "draw"
        is_draw = True
    elif winner_symbol == "X":
        status = "x_won"
        winner_id = game.player_x_id
    elif winner_symbol == "O":
        status = "o_won"
        winner_id = game.player_o_id

    game.status = status
    if winner_id:
        game.winner_id = winner_id
    if status in ("x_won", "o_won", "draw"):
        # Finalize game time & Insert match history
        from datetime import datetime
        game.end_time = datetime.utcnow()
        winner_id = game.winner_id if hasattr(game, 'winner_id') else None
        match_history = MatchHistory(
            game_id=game_id,
            player_x_id=game.player_x_id,
            player_o_id=game.player_o_id,
            winner_id=winner_id,
            result=status,
        )
        db.add(match_history)

    # Switch turn if still playing
    if status == "in_progress":
        game.current_turn = "O" if game.current_turn == "X" else "X"
    db.commit()
    db.refresh(game)
    return MoveResponse(
        board=board,
        status=status,
        winner=current_user.username if winner_id == current_user.id else None,
        is_draw=is_draw
    )

# PUBLIC_INTERFACE
@router.get(
    "/{game_id}",
    response_model=GameStateResponse,
    summary="Get current game state",
    description="Returns board state, status, moves, and player info for a given game.",
    responses={
        200: {"description": "Game details."},
        404: {"description": "Game not found."}
    },
)
def get_game_state(
    game_id: int = Path(..., description="ID of the game"),
    db: Session = Depends(get_session_factory()),
    current_user: User = Depends(get_current_user)
):
    """Get board state, move list, status, and player details for a game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")

    if game.player_x_id != current_user.id and \
       (game.player_o_id != current_user.id and game.player_o_id is not None):
        raise HTTPException(status_code=403, detail="Not authorized to view this game.")

    moves = db.query(Move).filter(Move.game_id == game_id).order_by(Move.move_number).all()
    board = reconstruct_board(moves)
    move_entries = [
        MoveEntry(
            move_number=m.move_number,
            player=db.query(User).filter(User.id == m.player_id).first().username,
            row=m.row,
            col=m.col,
            symbol=m.symbol,
            moved_at=m.moved_at.isoformat() if hasattr(m, "moved_at") else ""
        )
        for m in moves
    ]
    winner = None
    if game.winner_id:
        winner_user = db.query(User).filter(User.id == game.winner_id).first()
        winner = winner_user.username if winner_user else None
    is_draw = game.status == "draw"

    return GameStateResponse(
        game_id=game.id,
        board=board,
        current_turn=game.current_turn,
        status=game.status,
        moves=move_entries,
        player_x=db.query(User).filter(User.id == game.player_x_id).first().username,
        player_o=db.query(User).filter(User.id == game.player_o_id).first().username if game.player_o_id else None,
        winner=winner,
        is_draw=is_draw
    )

# PUBLIC_INTERFACE
@router.get(
    "/history",
    response_model=GameHistoryResponse,
    summary="Get match history for authenticated user",
    description="Returns summary info for all games involving the user (played as X or O).",
    responses={
        200: {"description": "History returned."}
    }
)
def get_game_history(
    db: Session = Depends(get_session_factory()),
    current_user: User = Depends(get_current_user)
):
    """Return a list of finished or abandoned games for the current user."""
    match_query = db.query(MatchHistory).filter(
        (MatchHistory.player_x_id == current_user.id) | (MatchHistory.player_o_id == current_user.id)
    ).order_by(MatchHistory.finished_at.desc())

    games = []
    for match in match_query:
        player_x = db.query(User).filter(User.id == match.player_x_id).first()
        player_o = db.query(User).filter(User.id == match.player_o_id).first() if match.player_o_id else None
        winner = db.query(User).filter(User.id == match.winner_id).first() if match.winner_id else None
        games.append(HistoryEntry(
            game_id=match.game_id,
            player_x=player_x.username if player_x else "",
            player_o=player_o.username if player_o else None,
            result=match.result,
            winner=winner.username if winner else None,
            finished_at=match.finished_at.isoformat() if match.finished_at else ""
        ))
    return GameHistoryResponse(games=games)
