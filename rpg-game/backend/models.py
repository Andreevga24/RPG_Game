"""
models.py — ALL SQLAlchemy models.
Tables are split across two databases:
  - players.db : User, Character
  - game.db    : Monster, City, RaidGroup, RaidMember, GateEvent, GateSchedule
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

# Two separate Base instances — one per database
PlayersBase = declarative_base()
GameBase    = declarative_base()


# ── Enums ─────────────────────────────────────────────────────────────────────
class RankEnum(str, enum.Enum):
    S = "S"; A = "A"; B = "B"; C = "C"; D = "D"; E = "E"

class ClassEnum(str, enum.Enum):
    TAURAN   = "Tauran"
    GNOMBAF  = "Gnombaf"
    ARACHNID = "Arachnid"
    ANGEL    = "Angel"


# ══════════════════════════════════════════════════════════════════════════════
# PLAYERS DB
# ══════════════════════════════════════════════════════════════════════════════
class User(PlayersBase):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String, unique=True, index=True)
    email           = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role            = Column(String, default="player")
    created_at      = Column(DateTime, default=datetime.utcnow)
    character       = relationship("Character", back_populates="user", uselist=False)

class Character(PlayersBase):
    __tablename__ = "characters"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), unique=True)
    name          = Column(String)
    rank          = Column(Enum(RankEnum), default=RankEnum.E)
    char_class    = Column(Enum(ClassEnum))
    level         = Column(Integer, default=1)
    exp           = Column(Integer, default=0)
    exp_next      = Column(Integer, default=100)
    hp            = Column(Integer, default=100)
    hp_max        = Column(Integer, default=100)
    energy        = Column(Integer, default=10)   # текущая энергия (WIS)
    energy_max    = Column(Integer, default=10)   # макс.; 10 + max(0, (wis-5)*2)
    gold          = Column(Integer, default=0)
    f1_points     = Column(Integer, default=0)
    last_regen_at = Column(DateTime, default=datetime.utcnow)
    stat_points   = Column(Integer, default=0)
    rank_points   = Column(Integer, default=0)
    str_          = Column("str", Integer, default=5)
    dex           = Column(Integer, default=5)
    con           = Column(Integer, default=5)
    int_          = Column("int", Integer, default=5)
    wis           = Column(Integer, default=5)
    cha           = Column(Integer, default=5)
    equipped_weapon_id = Column(String, nullable=True)
    equipped_armor_id  = Column(String, nullable=True)
    equipped_pet_id    = Column(String, nullable=True)
    battle_str_bonus   = Column(Integer, default=0)
    battle_def_bonus   = Column(Integer, default=0)
    battle_int_bonus   = Column(Integer, default=0)
    bonus_gold_pct_next = Column(Integer, default=0)
    user          = relationship("User", back_populates="character")


class InventoryItem(PlayersBase):
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_inventory_user_item"),)

    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    item_id  = Column(String, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)


# ══════════════════════════════════════════════════════════════════════════════
# GAME DB
# ══════════════════════════════════════════════════════════════════════════════
class Monster(GameBase):
    __tablename__ = "monsters"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String)
    rank       = Column(Enum(RankEnum))
    hp         = Column(Integer)
    attack     = Column(Integer)
    defense    = Column(Integer)
    exp_reward = Column(Integer)
    gold_reward= Column(Integer)
    city_id    = Column(Integer, ForeignKey("cities.id"))
    city       = relationship("City", back_populates="monsters")

class City(GameBase):
    __tablename__ = "cities"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String)
    description = Column(String)
    min_rank    = Column(Enum(RankEnum), default=RankEnum.E)
    monsters    = relationship("Monster", back_populates="city")

class RaidGroup(GameBase):
    __tablename__  = "raid_groups"
    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String)
    captain_id     = Column(Integer)   # user_id from players.db
    gate_event_id  = Column(Integer, ForeignKey("gate_events.id"), nullable=True)
    is_active      = Column(Boolean, default=True)
    started        = Column(Boolean, default=False)
    created_at     = Column(DateTime, default=datetime.utcnow)
    members        = relationship("RaidMember", back_populates="group")

class RaidMember(GameBase):
    __tablename__ = "raid_members"
    id            = Column(Integer, primary_key=True, index=True)
    group_id      = Column(Integer, ForeignKey("raid_groups.id"))
    user_id       = Column(Integer)   # user_id from players.db
    is_ready      = Column(Boolean, default=False)
    damage_dealt  = Column(Integer, default=0)
    group         = relationship("RaidGroup", back_populates="members")

class GateEvent(GameBase):
    __tablename__ = "gate_events"
    id            = Column(Integer, primary_key=True, index=True)
    rank          = Column(Enum(RankEnum))
    boss_name     = Column(String)
    boss_hp_max   = Column(Integer)
    boss_hp       = Column(Integer)
    opens_at      = Column(DateTime)
    closes_at     = Column(DateTime)
    is_active     = Column(Boolean, default=True)

class GateSchedule(GameBase):
    __tablename__  = "gate_schedule"
    id             = Column(Integer, primary_key=True, index=True)
    next_open_at   = Column(DateTime)
