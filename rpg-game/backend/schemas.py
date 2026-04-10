from pydantic import BaseModel, EmailStr
from typing import Optional
from models import RankEnum, ClassEnum

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CharacterCreate(BaseModel):
    name: str
    char_class: ClassEnum

class CharacterOut(BaseModel):
    id: int
    name: str
    rank: RankEnum
    char_class: ClassEnum
    level: int
    exp: int
    exp_next: int
    hp: int
    hp_max: int
    energy: int
    energy_max: int
    gold: int
    f1_points: int
    stat_points: int
    rank_points: int
    str_: int
    dex: int
    con: int
    int_: int
    wis: int
    cha: int
    equipped_weapon_id: Optional[str] = None
    equipped_armor_id: Optional[str] = None
    equipped_pet_id: Optional[str] = None

    class Config:
        from_attributes = True

class StatUpgrade(BaseModel):
    stat: str  # "str", "dex", "con", "int", "wis", "cha"

class MonsterOut(BaseModel):
    id: int
    name: str
    rank: RankEnum
    hp: int
    attack: int
    defense: int
    exp_reward: int
    gold_reward: int

    class Config:
        from_attributes = True

class CityOut(BaseModel):
    id: int
    name: str
    description: str
    min_rank: RankEnum
    monsters: list[MonsterOut]

    class Config:
        from_attributes = True

class FightRequest(BaseModel):
    monster_id: int

class FightResult(BaseModel):
    victory: bool
    log: list[str]
    exp_gained: int
    gold_gained: int
    hp_remaining: int

class RaidGroupCreate(BaseModel):
    name: str

class RaidMemberOut(BaseModel):
    user_id: int
    username: str
    char_class: str
    rank: str
    is_ready: bool
    damage_dealt: int = 0

    class Config:
        from_attributes = True

class RaidGroupOut(BaseModel):
    id: int
    name: str
    captain_id: int
    member_count: int
    members: list[RaidMemberOut]

class GateEventOut(BaseModel):
    id: int
    rank: str
    boss_name: str
    boss_hp_max: int
    boss_hp: int
    opens_at: str
    closes_at: str
    is_active: bool
    seconds_until_open: int
    seconds_until_close: int
    groups: list[RaidGroupOut]

class GateAttackResult(BaseModel):
    damage_dealt: int
    boss_hp: int
    boss_hp_max: int
    log: list[str]
    rank_points: int
    exp_gained: int
    gold_gained: int
    boss_defeated: bool

class LeaderboardEntry(BaseModel):
    rank_position: int
    username: str
    rank: str
    char_class: str
    f1_points: int
