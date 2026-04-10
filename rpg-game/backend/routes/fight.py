from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, get_game_db
from models import Character, Monster
from items_catalog import passive_equipment_bonuses, clear_battle_potion_bonuses
from schemas import FightRequest, FightResult
from auth import get_current_user_id
from routes.character import apply_regen, exp_for_level, MAX_LEVEL, STAT_POINTS_PER_LEVEL
import random

router = APIRouter(prefix="/api/fight", tags=["fight"])

FLEE_COST = 0  # энергия в бою не расходуется (резерв под способности)

@router.get("/random_monster")
def random_monster(city_id: int, user_id: int = Depends(get_current_user_id),
                   db: Session = Depends(get_db), game_db: Session = Depends(get_game_db)):
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    rank_order = ["E","D","C","B","A","S"]
    char_rank_idx = rank_order.index(char.rank.value) if char.rank.value in rank_order else 0
    monsters = game_db.query(Monster).filter(Monster.city_id == city_id).all()
    if not monsters:
        raise HTTPException(status_code=404, detail="No monsters in this city")
    def weight(m):
        idx = rank_order.index(m.rank.value) if m.rank.value in rank_order else 0
        return max(1, 10 - abs(idx - char_rank_idx) * 2)
    chosen = random.choices(monsters, weights=[weight(m) for m in monsters], k=1)[0]
    return {"id": chosen.id, "name": chosen.name, "rank": chosen.rank.value,
            "hp": chosen.hp, "attack": chosen.attack, "defense": chosen.defense,
            "exp_reward": chosen.exp_reward, "gold_reward": chosen.gold_reward}

@router.post("/flee")
def flee(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    if FLEE_COST:
        char.energy = max(0, char.energy - FLEE_COST)
    db.commit()
    return {"energy": char.energy, "energy_max": char.energy_max}

@router.post("", response_model=FightResult)
def start_fight(data: FightRequest, user_id: int = Depends(get_current_user_id),
                db: Session = Depends(get_db), game_db: Session = Depends(get_game_db)):
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    apply_regen(char, db)
    monster = game_db.query(Monster).filter(Monster.id == data.monster_id).first()
    if not monster:
        raise HTTPException(status_code=404, detail="Monster not found")

    log = []
    char_hp = char.hp
    mon_hp = monster.hp

    eq = passive_equipment_bonuses(char)
    b_str = char.battle_str_bonus or 0
    b_int = char.battle_int_bonus or 0
    b_def = char.battle_def_bonus or 0
    str_eff = max(0, char.str_ + eq["str"] + b_str)
    int_eff = char.int_ + eq["int"] + b_int
    char_atk = 5 + char.level * 2 + str_eff + (char.dex // 3)
    char_def = 3 + char.level + char.dex + (char.con // 3) + eq["def"] + b_def
    player_first = char.dex >= monster.attack // 3
    dodge_chance = min(25, char.dex // 4)
    crit_chance = min(30, int_eff // 3)

    def player_strike():
        nonlocal mon_hp
        raw = max(1, char_atk - monster.defense + random.randint(-3, 5))
        dmg = raw
        is_crit = random.randint(1, 100) <= crit_chance
        if is_crit:
            dmg = max(1, int(raw * 1.5))
        mon_hp -= dmg
        crit_tag = " КРИТ!" if is_crit else ""
        log.append(
            f"Раунд {round_num}: Вы наносите {dmg} урона{crit_tag} {monster.name}. HP монстра: {max(0, mon_hp)}"
        )
        return mon_hp <= 0

    def monster_strike():
        nonlocal char_hp
        if random.randint(1, 100) <= dodge_chance:
            log.append(f"Раунд {round_num}: Ты увернулся от атаки!")
            return
        dmg = max(1, monster.attack - char_def + random.randint(-2, 4))
        char_hp -= dmg
        log.append(f"Раунд {round_num}: {monster.name} наносит вам {dmg} урона. Ваше HP: {max(0, char_hp)}")

    round_num = 1
    while char_hp > 0 and mon_hp > 0 and round_num <= 20:
        if player_first:
            if player_strike(): break
            monster_strike()
        else:
            monster_strike()
            if player_strike(): break
        round_num += 1

    victory = mon_hp <= 0
    exp_gained = monster.exp_reward if victory else monster.exp_reward // 4
    gold_gained = monster.gold_reward if victory else 0
    if victory and (char.bonus_gold_pct_next or 0):
        pct = char.bonus_gold_pct_next or 0
        gold_gained = int(gold_gained * (100 + pct) / 100)
        char.bonus_gold_pct_next = 0

    # Update character (энергия в обычном бою не расходуется)
    char.hp = max(1, char_hp)
    hp_regen = max(1, char.con // 10)
    char.hp = min(char.hp_max, char.hp + hp_regen)
    char.exp += exp_gained
    char.gold += gold_gained
    clear_battle_potion_bonuses(char)

    # Level up check
    while char.exp >= char.exp_next and char.level < MAX_LEVEL:
        char.exp -= char.exp_next
        char.level += 1
        char.exp_next = exp_for_level(char.level)
        char.hp_max += 10
        char.hp = char.hp_max
        char.energy = char.energy_max
        char.stat_points += STAT_POINTS_PER_LEVEL
        log.append(f"🎉 Уровень {char.level}! +{STAT_POINTS_PER_LEVEL} очков характеристик. Следующий: {char.exp_next} опыта.")

    # Cap exp at max level
    if char.level >= MAX_LEVEL:
        char.exp = 0
        char.exp_next = 0

    if victory:
        char.f1_points += exp_gained // 10
        log.append(f"✅ Победа! Получено: {exp_gained} опыта, {gold_gained} золота.")
    else:
        log.append(f"💀 Поражение. Получено: {exp_gained} опыта.")

    db.commit()
    return FightResult(
        victory=victory,
        log=log,
        exp_gained=exp_gained,
        gold_gained=gold_gained,
        hp_remaining=char.hp
    )
