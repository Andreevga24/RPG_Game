from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, get_game_db
from models import RaidGroup, RaidMember, GateEvent, GateSchedule, Character, User, RankEnum
from schemas import RaidGroupCreate, RaidGroupOut, RaidMemberOut, GateEventOut, GateAttackResult
from auth import get_current_user_id
from routes.character import apply_regen, exp_for_level, MAX_LEVEL, STAT_POINTS_PER_LEVEL
from items_catalog import passive_equipment_bonuses, clear_battle_potion_bonuses
from datetime import datetime, timezone, timedelta
import random

router = APIRouter(prefix="/api/raid", tags=["raid"])

MAX_GROUP = 10
GATE_DURATION_HOURS = 4

# Boss config per rank
BOSS_CONFIG = {
    RankEnum.E: dict(name="Страж Врат",        hp=5_000,   atk=40,  defense=10, exp=500,  gold=200,  rank_pts=5),
    RankEnum.D: dict(name="Тёмный Привратник",  hp=15_000,  atk=70,  defense=20, exp=1000, gold=500,  rank_pts=10),
    RankEnum.C: dict(name="Демон Порога",       hp=40_000,  atk=120, defense=35, exp=2500, gold=1200, rank_pts=20),
    RankEnum.B: dict(name="Владыка Теней",      hp=100_000, atk=200, defense=60, exp=6000, gold=3000, rank_pts=40),
    RankEnum.A: dict(name="Архидемон Бездны",   hp=300_000, atk=350, defense=100,exp=15000,gold=8000, rank_pts=80),
    RankEnum.S: dict(name="Бог Разрушения",     hp=1_000_000,atk=600,defense=200,exp=50000,gold=30000,rank_pts=200),
}

# Minion counts per rank
MINION_COUNT = {RankEnum.E:3, RankEnum.D:5, RankEnum.C:8, RankEnum.B:12, RankEnum.A:16, RankEnum.S:20}


def get_or_create_gate(db: Session) -> GateEvent:
    """Return active gate or close expired one."""
    now = datetime.now(timezone.utc)
    gate = db.query(GateEvent).filter(GateEvent.is_active == True).first()
    if gate:
        closes = gate.closes_at.replace(tzinfo=timezone.utc) if gate.closes_at.tzinfo is None else gate.closes_at
        if now > closes:
            gate.is_active = False
            db.commit()
            # Schedule next opening
            _schedule_next(db)
            return None
        return gate
    return None


def _schedule_next(db: Session):
    """Create or update the next gate open time (random within next 20–24h)."""
    now = datetime.now(timezone.utc)
    delay_hours = random.uniform(20, 24)
    next_open = now + timedelta(hours=delay_hours)
    sched = db.query(GateSchedule).first()
    if sched:
        sched.next_open_at = next_open
    else:
        db.add(GateSchedule(next_open_at=next_open))
    db.commit()


def get_seconds_until_open(db: Session) -> int:
    """Return stable seconds until next gate open, creating schedule if missing."""
    now = datetime.now(timezone.utc)
    sched = db.query(GateSchedule).first()
    if not sched:
        _schedule_next(db)
        sched = db.query(GateSchedule).first()
    next_open = sched.next_open_at.replace(tzinfo=timezone.utc) if sched.next_open_at.tzinfo is None else sched.next_open_at
    # If scheduled time already passed — open the gate now
    if now >= next_open:
        return 0
    return max(0, int((next_open - now).total_seconds()))


def create_gate(db: Session) -> GateEvent:
    """Spawn a new gate with random rank."""
    now = datetime.now(timezone.utc)
    rank = random.choices(
        list(RankEnum),
        weights=[40, 25, 18, 10, 5, 2],  # E D C B A S
        k=1
    )[0]
    cfg = BOSS_CONFIG[rank]
    opens_at  = now
    closes_at = now + timedelta(hours=GATE_DURATION_HOURS)
    gate = GateEvent(
        rank=rank,
        boss_name=cfg["name"],
        boss_hp_max=cfg["hp"],
        boss_hp=cfg["hp"],
        opens_at=opens_at,
        closes_at=closes_at,
        is_active=True,
    )
    db.add(gate)
    db.commit()
    db.refresh(gate)
    return gate


def gate_to_out(gate: GateEvent, db: Session) -> GateEventOut:
    now = datetime.now(timezone.utc)
    opens  = gate.opens_at.replace(tzinfo=timezone.utc)  if gate.opens_at.tzinfo  is None else gate.opens_at
    closes = gate.closes_at.replace(tzinfo=timezone.utc) if gate.closes_at.tzinfo is None else gate.closes_at
    sec_open  = max(0, int((opens  - now).total_seconds()))
    sec_close = max(0, int((closes - now).total_seconds()))

    groups = db.query(RaidGroup).filter(
        RaidGroup.gate_event_id == gate.id,
        RaidGroup.is_active == True
    ).all()
    group_list = []
    for g in groups:
        members = db.query(RaidMember).filter(RaidMember.group_id == g.id).all()
        member_out = []
        for m in members:
            u = db.query(User).filter(User.id == m.user_id).first()
            c = db.query(Character).filter(Character.user_id == m.user_id).first()
            if u and c:
                member_out.append(RaidMemberOut(
                    user_id=m.user_id, username=u.username,
                    char_class=c.char_class.value, rank=c.rank.value,
                    is_ready=m.is_ready, damage_dealt=m.damage_dealt
                ))
        group_list.append(RaidGroupOut(
            id=g.id, name=g.name, captain_id=g.captain_id,
            member_count=len(members), members=member_out
        ))

    return GateEventOut(
        id=gate.id, rank=gate.rank.value,
        boss_name=gate.boss_name,
        boss_hp_max=gate.boss_hp_max, boss_hp=gate.boss_hp,
        opens_at=opens.isoformat(), closes_at=closes.isoformat(),
        is_active=gate.is_active,
        seconds_until_open=sec_open,
        seconds_until_close=sec_close,
        groups=group_list,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/status")
def raid_status(user_id: int = Depends(get_current_user_id), game_db: Session = Depends(get_game_db)):
    gate = get_or_create_gate(game_db)
    if gate:
        return {"gate": gate_to_out(gate, game_db), "is_open": True}
    seconds = get_seconds_until_open(game_db)
    if seconds == 0:
        gate = create_gate(game_db)
        sched = game_db.query(GateSchedule).first()
        if sched:
            game_db.delete(sched)
            game_db.commit()
        return {"gate": gate_to_out(gate, game_db), "is_open": True}
    return {"gate": None, "is_open": False, "seconds_until_open": seconds}


@router.post("/open")
def force_open_gate(user_id: int = Depends(get_current_user_id), game_db: Session = Depends(get_game_db)):
    existing = get_or_create_gate(game_db)
    if existing:
        return gate_to_out(existing, game_db)
    gate = create_gate(game_db)
    sched = game_db.query(GateSchedule).first()
    if sched:
        game_db.delete(sched)
        game_db.commit()
    return gate_to_out(gate, game_db)


@router.post("/group")
def create_group(data: RaidGroupCreate, user_id: int = Depends(get_current_user_id),
                 db: Session = Depends(get_db), game_db: Session = Depends(get_game_db)):
    gate = get_or_create_gate(game_db)
    if not gate:
        raise HTTPException(status_code=400, detail="Врата закрыты")
    existing = game_db.query(RaidMember).join(RaidGroup).filter(
        RaidMember.user_id == user_id,
        RaidGroup.gate_event_id == gate.id,
        RaidGroup.is_active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже в группе")
    group = RaidGroup(name=data.name, captain_id=user_id, gate_event_id=gate.id)
    game_db.add(group)
    game_db.flush()
    game_db.add(RaidMember(group_id=group.id, user_id=user_id, is_ready=True))
    game_db.commit()
    game_db.refresh(group)
    u = db.query(User).filter(User.id == user_id).first()
    c = db.query(Character).filter(Character.user_id == user_id).first()
    return RaidGroupOut(
        id=group.id, name=group.name, captain_id=group.captain_id, member_count=1,
        members=[RaidMemberOut(user_id=user_id, username=u.username,
                               char_class=c.char_class.value, rank=c.rank.value,
                               is_ready=True, damage_dealt=0)]
    )


@router.post("/group/{group_id}/join")
def join_group(group_id: int, user_id: int = Depends(get_current_user_id),
               game_db: Session = Depends(get_game_db)):
    gate = get_or_create_gate(game_db)
    if not gate:
        raise HTTPException(status_code=400, detail="Врата закрыты")
    group = game_db.query(RaidGroup).filter(RaidGroup.id == group_id, RaidGroup.is_active == True).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    if game_db.query(RaidMember).filter(RaidMember.group_id == group_id).count() >= MAX_GROUP:
        raise HTTPException(status_code=400, detail="Группа заполнена (макс. 10)")
    if game_db.query(RaidMember).filter(RaidMember.group_id == group_id, RaidMember.user_id == user_id).first():
        raise HTTPException(status_code=400, detail="Вы уже в этой группе")
    game_db.add(RaidMember(group_id=group_id, user_id=user_id))
    game_db.commit()
    return {"message": "Вступили в группу"}


@router.post("/group/{group_id}/leave")
def leave_group(group_id: int, user_id: int = Depends(get_current_user_id),
                game_db: Session = Depends(get_game_db)):
    member = game_db.query(RaidMember).filter(RaidMember.group_id == group_id, RaidMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Вы не в этой группе")
    game_db.delete(member)
    game_db.commit()
    return {"message": "Покинули группу"}


@router.post("/attack", response_model=GateAttackResult)
def attack_gate(user_id: int = Depends(get_current_user_id),
                db: Session = Depends(get_db), game_db: Session = Depends(get_game_db)):
    gate = get_or_create_gate(game_db)
    if not gate:
        raise HTTPException(status_code=400, detail="Врата закрыты")
    if gate.boss_hp <= 0:
        raise HTTPException(status_code=400, detail="Босс уже повержен")

    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Персонаж не найден")
    apply_regen(char, db)

    cfg = BOSS_CONFIG[gate.rank]
    log = []

    member = game_db.query(RaidMember).join(RaidGroup).filter(
        RaidMember.user_id == user_id,
        RaidGroup.gate_event_id == gate.id,
        RaidGroup.is_active == True,
    ).first()
    if member:
        mids = [m.user_id for m in game_db.query(RaidMember).filter(RaidMember.group_id == member.group_id).all()]
        party_chars = [db.query(Character).filter(Character.user_id == uid).first() for uid in mids]
        party_chars = [c for c in party_chars if c]
    else:
        party_chars = [char]
    leadership_bonus = min(5, sum(c.cha // 4 for c in party_chars))

    eq = passive_equipment_bonuses(char)
    b_str = char.battle_str_bonus or 0
    b_int = char.battle_int_bonus or 0
    b_def = char.battle_def_bonus or 0
    str_eff = max(0, char.str_ + eq["str"] + b_str)
    int_eff = char.int_ + eq["int"] + b_int
    char_atk = (
        5 + char.level * 3 + str_eff + char.dex // 2 + int_eff // 2 + leadership_bonus
    )
    initiative_bonus = char.cha // 5
    atk_threshold = cfg["atk"] // 3
    player_first = (char.dex + initiative_bonus) >= atk_threshold
    log.append(
        f"Инициатива (рейд): {char.dex + initiative_bonus} ≥ {atk_threshold} — "
        f"{'вы действуете первым' if player_first else 'босс давит'}"
    )
    log.append(f"Лидерство партии: +{leadership_bonus} к атаке (харизма, макс. 5)")

    boss_def = cfg["defense"]
    total_dmg = 0
    for i in range(1, 6):
        dmg = max(1, char_atk - boss_def + random.randint(-5, 15))
        total_dmg += dmg
        log.append(f"Удар {i}: {dmg} урона по {gate.boss_name}")

    raid_def = 3 + char.level + char.dex + char.con // 3 + eq["def"] + b_def
    boss_dmg = max(1, cfg["atk"] - raid_def + random.randint(-10, 20))
    char.hp  = max(1, char.hp - boss_dmg)
    log.append(f"💥 {gate.boss_name} наносит вам {boss_dmg} урона")

    gate.boss_hp = max(0, gate.boss_hp - total_dmg)

    hp_pct      = total_dmg / gate.boss_hp_max
    exp_gained  = int(cfg["exp"]  * hp_pct * 10)
    gold_gained = int(cfg["gold"] * hp_pct * 10)
    rank_pts    = max(1, int(cfg["rank_pts"] * hp_pct * 10))

    char.exp         += exp_gained
    char.gold        += gold_gained
    char.rank_points += rank_pts
    char.f1_points   += rank_pts

    while char.exp >= char.exp_next and char.level < MAX_LEVEL:
        char.exp -= char.exp_next
        char.level += 1
        char.exp_next = exp_for_level(char.level)
        char.hp_max += 10
        char.hp = char.hp_max
        char.energy = char.energy_max
        char.stat_points += STAT_POINTS_PER_LEVEL
        log.append(f"🎉 Уровень {char.level}!")

    if member:
        member.damage_dealt += total_dmg

    boss_defeated = gate.boss_hp <= 0
    if boss_defeated:
        log.append(f"💀 {gate.boss_name} повержен!")
        gate.is_active = False
        char.rank_points += cfg["rank_pts"]
        char.gold        += cfg["gold"]
        rank_pts         += cfg["rank_pts"]
        _schedule_next(game_db)

    clear_battle_potion_bonuses(char)
    db.commit()
    game_db.commit()
    log.append(f"HP босса: {gate.boss_hp:,}/{gate.boss_hp_max:,}")

    return GateAttackResult(
        damage_dealt=total_dmg, boss_hp=gate.boss_hp, boss_hp_max=gate.boss_hp_max,
        log=log, rank_points=rank_pts, exp_gained=exp_gained,
        gold_gained=gold_gained, boss_defeated=boss_defeated,
    )
