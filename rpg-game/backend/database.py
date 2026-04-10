from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

# ── Players DB — never delete, stores users & characters ─────────────────────
PLAYERS_DB_URL = os.getenv("PLAYERS_DB_URL", "sqlite:///./players.db")

# ── Game DB — game world data: cities, monsters, raids, gates ────────────────
GAME_DB_URL = os.getenv("GAME_DB_URL", "sqlite:///./game.db")

_connect_args = {"check_same_thread": False}

players_engine = create_engine(PLAYERS_DB_URL, connect_args=_connect_args)
game_engine    = create_engine(GAME_DB_URL,    connect_args=_connect_args)

PlayersSession = sessionmaker(autocommit=False, autoflush=False, bind=players_engine)
GameSession    = sessionmaker(autocommit=False, autoflush=False, bind=game_engine)

# Legacy alias — routes that haven't been split yet use this
engine     = players_engine
SessionLocal = PlayersSession

def get_db():
    """Default session — players DB (users, characters)."""
    db = PlayersSession()
    try:
        yield db
    finally:
        db.close()

def get_game_db():
    """Game world session — cities, monsters, raids, gates."""
    db = GameSession()
    try:
        yield db
    finally:
        db.close()


def migrate_players_schema():
    """Добавляет новые колонки в SQLite без Alembic (для существующих players.db)."""
    from sqlalchemy import inspect, text

    insp = inspect(players_engine)
    tables = insp.get_table_names()
    if "characters" not in tables:
        return
    cols = {c["name"] for c in insp.get_columns("characters")}
    alters = [
        ("equipped_weapon_id", "VARCHAR"),
        ("equipped_armor_id", "VARCHAR"),
        ("equipped_pet_id", "VARCHAR"),
        ("battle_str_bonus", "INTEGER DEFAULT 0"),
        ("battle_def_bonus", "INTEGER DEFAULT 0"),
        ("battle_int_bonus", "INTEGER DEFAULT 0"),
        ("bonus_gold_pct_next", "INTEGER DEFAULT 0"),
    ]
    with players_engine.begin() as conn:
        for col, typ in alters:
            if col not in cols:
                conn.execute(text(f"ALTER TABLE characters ADD COLUMN {col} {typ}"))
