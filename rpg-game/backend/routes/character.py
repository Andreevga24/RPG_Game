from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Character, RankEnum, ClassEnum
from schemas import CharacterCreate, CharacterOut, StatUpgrade
from auth import get_current_user_id
from datetime import datetime, timezone
import random

router = APIRouter(prefix="/api/character", tags=["character"])

RANK_WEIGHTS = {
    RankEnum.E: 40, RankEnum.D: 25, RankEnum.C: 18,
    RankEnum.B: 10, RankEnum.A: 5, RankEnum.S: 2
}
RANK_HP = {RankEnum.E: 80, RankEnum.D: 100, RankEnum.C: 130,
           RankEnum.B: 170, RankEnum.A: 220, RankEnum.S: 300}


def energy_max_for_wis(wis: int) -> int:
    """База 10; каждое WIS выше 5 даёт +2 к макс. энергии."""
    return 10 + max(0, (wis - 5) * 2)


def sync_energy_max_from_wis(char: Character, db: Session) -> None:
    """Приводит energy_max к формуле от WIS (миграция и консистентность)."""
    expected = energy_max_for_wis(char.wis)
    if char.energy_max == expected:
        return
    char.energy_max = expected
    char.energy = min(char.energy, char.energy_max)
    db.commit()

# Base stats per class (str, dex, con, int, wis, cha)
CLASS_STATS = {
    # Тауран — физик, дубина, без магии. STR/CON максимум, INT минимум
    ClassEnum.TAURAN:   dict(str_=14, dex=4,  con=12, int_=2,  wis=3,  cha=5),
    # Гномбаф — маг-баффер, площадные заклинания. INT/WIS максимум
    ClassEnum.GNOMBAF:  dict(str_=3,  dex=5,  con=4,  int_=13, wis=11, cha=4),
    # Арахнид — ловкач, скрытность, яд. DEX максимум
    ClassEnum.ARACHNID: dict(str_=5,  dex=15, con=4,  int_=6,  wis=5,  cha=5),
    # Ангел — хилер/поддержка, справедливость. WIS/CHA максимум
    ClassEnum.ANGEL:    dict(str_=4,  dex=6,  con=6,  int_=7,  wis=12, cha=11),
}

FULL_REGEN_HOURS = 6
FULL_REGEN_SECONDS = FULL_REGEN_HOURS * 3600
VALID_STATS = {"str", "dex", "con", "int", "wis", "cha", "hp"}
MAX_LEVEL = 85
STAT_POINTS_PER_LEVEL = 10

# Rank progression: points needed to reach next rank
RANK_ORDER = [RankEnum.E, RankEnum.D, RankEnum.C, RankEnum.B, RankEnum.A, RankEnum.S]
RANK_UP_COST = {RankEnum.E: 10, RankEnum.D: 25, RankEnum.C: 50, RankEnum.B: 100, RankEnum.A: 200}

def exp_for_level(level: int) -> int:
    """EXP needed to reach next level. Level 1→2 = 100, grows exponentially."""
    return int(100 * (1.7 ** (level - 1)))

def apply_regen(char: Character, db: Session) -> None:
    now = datetime.now(timezone.utc)
    last = char.last_regen_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    elapsed_seconds = max(0.0, (now - last).total_seconds())
    hp_regen = int((elapsed_seconds * char.hp_max) / FULL_REGEN_SECONDS)
    energy_regen = int((elapsed_seconds * char.energy_max) / FULL_REGEN_SECONDS)
    if hp_regen <= 0 and energy_regen <= 0:
        return
    new_hp = min(char.hp_max, char.hp + hp_regen)
    new_energy = min(char.energy_max, char.energy + energy_regen)
    if new_hp != char.hp or new_energy != char.energy:
        char.hp = new_hp
        char.energy = new_energy
        char.last_regen_at = now
        db.commit()

def _attr(stat: str) -> str:
    """Map API stat name to model attribute name."""
    return {"str": "str_", "int": "int_"}.get(stat, stat)

def get_stat(char: Character, stat: str) -> int:
    return getattr(char, _attr(stat))

def set_stat(char: Character, stat: str, value: int):
    setattr(char, _attr(stat), value)

@router.get("/roll")
def roll_character(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    ranks = list(RANK_WEIGHTS.keys())
    weights = list(RANK_WEIGHTS.values())
    rank = random.choices(ranks, weights=weights, k=1)[0]
    char_class = random.choice(list(ClassEnum))
    return {"rank": rank, "char_class": char_class}

@router.post("", response_model=CharacterOut)
def create_character(data: CharacterCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    existing = db.query(Character).filter(Character.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Character already exists")
    # All new characters start at rank E
    rank = RankEnum.E
    base_hp = RANK_HP.get(rank, 80)
    stats = CLASS_STATS.get(data.char_class, {})
    con_val = stats.get("con", 5)
    wis_val = stats.get("wis", 5)
    hp = base_hp + (con_val - 5) * 5
    em = energy_max_for_wis(wis_val)
    char = Character(
        user_id=user_id,
        name=data.name,
        rank=rank,
        char_class=data.char_class,
        hp=hp, hp_max=hp,
        energy=em, energy_max=em,
        last_regen_at=datetime.now(timezone.utc),
        exp_next=exp_for_level(1),
        stat_points=5,
        rank_points=0,
        **stats
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char

@router.get("", response_model=CharacterOut)
def get_character(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    apply_regen(char, db)
    sync_energy_max_from_wis(char, db)
    db.refresh(char)
    return char

@router.post("/upgrade", response_model=CharacterOut)
def upgrade_stat(data: StatUpgrade, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if data.stat not in VALID_STATS:
        raise HTTPException(status_code=400, detail=f"Invalid stat. Choose from: {VALID_STATS}")
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if char.stat_points <= 0:
        raise HTTPException(status_code=400, detail="No stat points available")
    # HP is a special virtual stat — no model column, handled separately below
    if data.stat != "hp":
        old_wis = char.wis if data.stat == "wis" else None
        current = get_stat(char, data.stat)
        set_stat(char, data.stat, current + 1)
        if data.stat == "wis" and old_wis is not None:
            delta = energy_max_for_wis(char.wis) - energy_max_for_wis(old_wis)
            char.energy_max = energy_max_for_wis(char.wis)
            char.energy += delta
    char.stat_points -= 1
    # CON upgrade also increases max HP
    if data.stat == "con":
        char.hp_max += 5
        char.hp = min(char.hp + 5, char.hp_max)
    # HP upgrade: +20 max HP per point
    if data.stat == "hp":
        char.hp_max += 20
        char.hp = min(char.hp + 20, char.hp_max)
    db.commit()
    db.refresh(char)
    return char

@router.post("/rank_up", response_model=CharacterOut)
def rank_up(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if char.rank == RankEnum.S:
        raise HTTPException(status_code=400, detail="Already at max rank")
    current_idx = RANK_ORDER.index(char.rank)
    cost = RANK_UP_COST.get(char.rank)
    if char.rank_points < cost:
        raise HTTPException(status_code=400, detail=f"Need {cost} rank points, have {char.rank_points}")
    char.rank_points -= cost
    char.rank = RANK_ORDER[current_idx + 1]
    # Bonus HP on rank up; энергия — по WIS
    char.hp_max += RANK_HP.get(char.rank, 0) - RANK_HP.get(RANK_ORDER[current_idx], 0)
    char.hp = char.hp_max
    char.energy_max = energy_max_for_wis(char.wis)
    char.energy = char.energy_max
    db.commit()
    db.refresh(char)
    return char
