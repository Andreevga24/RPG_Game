from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Character, InventoryItem
from auth import get_current_user_id
from items_catalog import ITEMS, get_item, shop_item_public, passive_equipment_bonuses
from pydantic import BaseModel, Field
from routes.character import apply_regen

router = APIRouter(prefix="/api", tags=["shop"])


class BuyRequest(BaseModel):
    item_id: str
    quantity: int = Field(1, ge=1, le=99)


class UseItemRequest(BaseModel):
    item_id: str


class UnequipRequest(BaseModel):
    slot: str  # weapon | armor | pet


def _inv_row(db: Session, user_id: int, item_id: str) -> InventoryItem | None:
    return (
        db.query(InventoryItem)
        .filter(InventoryItem.user_id == user_id, InventoryItem.item_id == item_id)
        .first()
    )


def _apply_consumable(char: Character, effect: dict) -> str:
    parts: list[str] = []
    if "heal_hp" in effect:
        add = int(effect["heal_hp"])
        before = char.hp
        char.hp = min(char.hp_max, char.hp + add)
        parts.append(f"HP +{char.hp - before}")
    if "heal_hp_pct" in effect:
        add = max(1, int(char.hp_max * int(effect["heal_hp_pct"]) / 100))
        before = char.hp
        char.hp = min(char.hp_max, char.hp + add)
        parts.append(f"HP +{char.hp - before}")
    if "restore_energy_ratio" in effect:
        ratio = float(effect["restore_energy_ratio"])
        mn = int(effect.get("restore_energy_min", 0))
        gain = max(mn, int(char.energy_max * ratio))
        before = char.energy
        char.energy = min(char.energy_max, char.energy + gain)
        parts.append(f"Энергия +{char.energy - before}")
    if "battle_str" in effect:
        char.battle_str_bonus = int(effect["battle_str"])
        parts.append("Сила в следующем бою усилена")
    if "battle_def" in effect:
        char.battle_def_bonus = int(effect["battle_def"])
        parts.append("Защита в следующем бою усилена")
    if "battle_int" in effect:
        char.battle_int_bonus = int(effect["battle_int"])
        parts.append("Интеллект для крита в следующем бою усилен")
    if "next_arena_gold_pct" in effect:
        char.bonus_gold_pct_next = int(effect["next_arena_gold_pct"])
        parts.append("Бонус золота с ближайшей победы на арене")
    return ", ".join(parts) if parts else "Эффект применён"


def _equipment_payload(char: Character) -> dict:
    bon = passive_equipment_bonuses(char)
    return {
        "weapon_id": char.equipped_weapon_id,
        "armor_id": char.equipped_armor_id,
        "pet_id": char.equipped_pet_id,
        "bonuses": bon,
    }


def shop_catalog_response() -> dict:
    """Каталог магазина (используется и роутером, и явным маршрутом в main)."""
    by_cat: dict[str, list[dict]] = {}
    for iid, meta in ITEMS.items():
        cat = meta["category"]
        pub = shop_item_public(iid)
        if pub:
            by_cat.setdefault(cat, []).append(pub)
    order = ["potion", "weapon", "armor", "pet", "misc"]
    return {"categories": [{"id": c, "items": by_cat[c]} for c in order if c in by_cat]}


@router.get("/inventory")
def get_inventory(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    apply_regen(char, db)
    rows = db.query(InventoryItem).filter(InventoryItem.user_id == user_id).all()
    items = []
    for r in rows:
        if r.quantity <= 0:
            continue
        pub = shop_item_public(r.item_id)
        if not pub:
            continue
        items.append({**pub, "quantity": r.quantity})
    return {
        "items": items,
        "equipment": _equipment_payload(char),
        "gold": char.gold,
    }


@router.post("/inventory/buy")
def buy_item(data: BuyRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    meta = get_item(data.item_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Unknown item")
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    stack_max = int(meta.get("stack_max", 99))
    row = _inv_row(db, user_id, data.item_id)
    cur = row.quantity if row else 0
    if cur + data.quantity > stack_max:
        raise HTTPException(status_code=400, detail=f"Лимит стака: {stack_max}")
    cost = int(meta["price"]) * data.quantity
    if char.gold < cost:
        raise HTTPException(status_code=400, detail="Недостаточно золота")
    char.gold -= cost
    if row:
        row.quantity += data.quantity
    else:
        db.add(InventoryItem(user_id=user_id, item_id=data.item_id, quantity=data.quantity))
    db.commit()
    return {"ok": True, "gold": char.gold, "spent": cost}


@router.post("/inventory/use")
def use_item(data: UseItemRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    meta = get_item(data.item_id)
    if not meta or not meta.get("consumable"):
        raise HTTPException(status_code=400, detail="Предмет нельзя использовать")
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    row = _inv_row(db, user_id, data.item_id)
    if not row or row.quantity < 1:
        raise HTTPException(status_code=400, detail="Нет предмета в инвентаре")
    effect = meta.get("effect") or {}
    msg = _apply_consumable(char, effect)
    row.quantity -= 1
    if row.quantity <= 0:
        db.delete(row)
    db.commit()
    db.refresh(char)
    return {
        "ok": True,
        "message": msg,
        "hp": char.hp,
        "hp_max": char.hp_max,
        "energy": char.energy,
        "energy_max": char.energy_max,
    }


@router.post("/inventory/equip")
def equip_item(data: UseItemRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    meta = get_item(data.item_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Unknown item")
    slot = meta.get("equippable")
    if not slot:
        raise HTTPException(status_code=400, detail="Нельзя экипировать")
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    row = _inv_row(db, user_id, data.item_id)
    if not row or row.quantity < 1:
        raise HTTPException(status_code=400, detail="Нет предмета в инвентаре")
    attr = {"weapon": "equipped_weapon_id", "armor": "equipped_armor_id", "pet": "equipped_pet_id"}[slot]
    setattr(char, attr, data.item_id)
    db.commit()
    db.refresh(char)
    return {"ok": True, "equipment": _equipment_payload(char)}


@router.post("/inventory/unequip")
def unequip_item(data: UnequipRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if data.slot not in ("weapon", "armor", "pet"):
        raise HTTPException(status_code=400, detail="Неверный слот")
    char = db.query(Character).filter(Character.user_id == user_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    attr = {"weapon": "equipped_weapon_id", "armor": "equipped_armor_id", "pet": "equipped_pet_id"}[data.slot]
    setattr(char, attr, None)
    db.commit()
    db.refresh(char)
    return {"ok": True, "equipment": _equipment_payload(char)}
