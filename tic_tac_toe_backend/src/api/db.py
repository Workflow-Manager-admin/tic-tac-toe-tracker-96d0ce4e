import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    ForeignKey,
    TIMESTAMP,
    func,
    UniqueConstraint,
    SmallInteger,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
from dotenv import load_dotenv

# Load environment variables from .env (.env should be in the project root)
load_dotenv()

# PUBLIC_INTERFACE
def get_database_url():
    """
    Build database URL using environment variables for connection.
    """
    user = os.getenv("DB_USER")
    pw = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")
    return f"mysql+mysqlconnector://{user}:{pw}@{host}:{port}/{db}"

# SQLAlchemy base class
Base = declarative_base()

# PUBLIC_INTERFACE
def get_engine():
    """Create SQLAlchemy engine using environment variables."""
    return create_engine(get_database_url(), pool_pre_ping=True, future=True)

# PUBLIC_INTERFACE
def get_session_factory():
    """
    Return a SQLAlchemy session factory (scoped_session) bound to the engine.
    """
    return scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=get_engine()))

# ------------------
# ORM Models
# ------------------

class User(Base):
    """User table: Stores registered user credentials and profile info."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(32), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    games_x = relationship("Game", foreign_keys="Game.player_x_id", back_populates="player_x")
    games_o = relationship("Game", foreign_keys="Game.player_o_id", back_populates="player_o")

    moves = relationship("Move", back_populates="player")
    match_history_x = relationship("MatchHistory", foreign_keys="MatchHistory.player_x_id", back_populates="player_x")
    match_history_o = relationship("MatchHistory", foreign_keys="MatchHistory.player_o_id", back_populates="player_o")
    match_history_winner = relationship("MatchHistory", foreign_keys="MatchHistory.winner_id", back_populates="winner")

class Game(Base):
    """Games table: Stores info about ongoing or completed games."""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    player_x_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_o_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(
        Enum("waiting", "in_progress", "x_won", "o_won", "draw", "abandoned", name="game_status"),
        nullable=False,
        server_default="waiting",
    )
    current_turn = Column(Enum("X", "O", name="current_turn"), server_default="X")
    start_time = Column(DateTime, server_default=func.current_timestamp())
    end_time = Column(DateTime, nullable=True, default=None)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True, default=None)
    game_mode = Column(Enum("vs_player", "vs_computer", name="game_mode"), server_default="vs_player")

    # Relationships
    player_x = relationship("User", foreign_keys=[player_x_id], back_populates="games_x")
    player_o = relationship("User", foreign_keys=[player_o_id], back_populates="games_o")
    winner = relationship("User", foreign_keys=[winner_id])

    moves = relationship("Move", back_populates="game", cascade="all, delete-orphan")
    match_history = relationship("MatchHistory", back_populates="game", uselist=False)

class Move(Base):
    """Moves table: Stores every move for move-by-move history."""
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    move_number = Column(Integer, nullable=False)
    player_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    row = Column(SmallInteger, nullable=False)  # 0, 1, or 2
    col = Column(SmallInteger, nullable=False)  # 0, 1, or 2
    symbol = Column(Enum("X", "O", name="move_symbol"), nullable=False)
    moved_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    game = relationship("Game", back_populates="moves")
    player = relationship("User", back_populates="moves")

    __table_args__ = (
        UniqueConstraint("game_id", "move_number", name="uq_game_id_move_number"),
    )

class MatchHistory(Base):
    """Match history table: Summary result for finished games."""
    __tablename__ = "match_history"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    player_x_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_o_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    result = Column(
        Enum("x_won", "o_won", "draw", "abandoned", name="match_result"), nullable=False
    )
    finished_at = Column(DateTime, server_default=func.current_timestamp())

    # Relationships
    game = relationship("Game", back_populates="match_history")
    player_x = relationship("User", foreign_keys=[player_x_id], back_populates="match_history_x")
    player_o = relationship("User", foreign_keys=[player_o_id], back_populates="match_history_o")
    winner = relationship("User", foreign_keys=[winner_id], back_populates="match_history_winner")

# PUBLIC_INTERFACE
def init_db():
    """Create all tables in the database (to be used during setup, not in production)."""
    engine = get_engine()
    Base.metadata.create_all(engine)
