"""
Каталог предметов магазина (кодовые id → описание, цена, эффекты).
"""
from __future__ import annotations

from typing import Any

# id → meta
ITEMS: dict[str, dict[str, Any]] = {
    # ── Зелья ─────────────────────────────────────────────────────────────
    "potion_hp_small": {
        "name": "Малое зелье жизни",
        "description": "Восстанавливает 45 HP.",
        "category": "potion",
        "price": 28,
        "stack_max": 99,
        "consumable": True,
        "effect": {"heal_hp": 45},
    },
    "potion_hp_large": {
        "name": "Большое зелье жизни",
        "description": "Восстанавливает 130 HP.",
        "category": "potion",
        "price": 85,
        "stack_max": 99,
        "consumable": True,
        "effect": {"heal_hp": 130},
    },
    "potion_energy": {
        "name": "Зелье бодрости",
        "description": "Восстанавливает энергию: 50% от максимума (не меньше 6).",
        "category": "potion",
        "price": 32,
        "stack_max": 99,
        "consumable": True,
        "effect": {"restore_energy_ratio": 0.5, "restore_energy_min": 6},
    },
    "potion_might": {
        "name": "Эликсир силы",
        "description": "Следующий бой (арена или рейд): +4 к силе в расчёте урона.",
        "category": "potion",
        "price": 52,
        "stack_max": 20,
        "consumable": True,
        "effect": {"battle_str": 4},
    },
    "potion_iron": {
        "name": "Зелье каменной кожи",
        "description": "Следующий бой: +3 к защите.",
        "category": "potion",
        "price": 48,
        "stack_max": 20,
        "consumable": True,
        "effect": {"battle_def": 3},
    },
    "potion_fortune": {
        "name": "Настойка удачи",
        "description": "С ближайшей победы на арене +35% к выпавшему золоту.",
        "category": "potion",
        "price": 75,
        "stack_max": 10,
        "consumable": True,
        "effect": {"next_arena_gold_pct": 35},
    },
    "potion_hybrid": {
        "name": "Смесь странника",
        "description": "Восстанавливает 30% HP и 35% макс. энергии (мин. 4 энергии).",
        "category": "potion",
        "price": 60,
        "stack_max": 30,
        "consumable": True,
        "effect": {"heal_hp_pct": 30, "restore_energy_ratio": 0.35, "restore_energy_min": 4},
    },
    "potion_mind": {
        "name": "Капля прозрения",
        "description": "Следующий бой: +3 к интеллекту в расчёте крита.",
        "category": "potion",
        "price": 44,
        "stack_max": 20,
        "consumable": True,
        "effect": {"battle_int": 3},
    },
    # ── Оружие ─────────────────────────────────────────────────────────────
    "weapon_rusty": {
        "name": "Ржавый клинок",
        "description": "Простой меч. +1 к силе в бою.",
        "category": "weapon",
        "price": 90,
        "stack_max": 1,
        "consumable": False,
        "equippable": "weapon",
        "bonus_str": 1,
    },
    "weapon_iron": {
        "name": "Железный меч",
        "description": "Надёжное оружие. +2 к силе.",
        "category": "weapon",
        "price": 240,
        "stack_max": 1,
        "consumable": False,
        "equippable": "weapon",
        "bonus_str": 2,
    },
    "weapon_steel": {
        "name": "Стальной клинок",
        "description": "Качественная сталь. +3 к силе.",
        "category": "weapon",
        "price": 520,
        "stack_max": 1,
        "consumable": False,
        "equippable": "weapon",
        "bonus_str": 3,
    },
    "weapon_arcane_wand": {
        "name": "Жезл ученика",
        "description": "Усиливает магию. +2 к интеллекту в расчёте крита.",
        "category": "weapon",
        "price": 210,
        "stack_max": 1,
        "consumable": False,
        "equippable": "weapon",
        "bonus_int": 2,
    },
    # ── Броня ───────────────────────────────────────────────────────────────
    "armor_cloth": {
        "name": "Лохмотья",
        "description": "Чуть лучше ничего. +1 к защите.",
        "category": "armor",
        "price": 65,
        "stack_max": 1,
        "consumable": False,
        "equippable": "armor",
        "bonus_def": 1,
    },
    "armor_leather": {
        "name": "Кожаный доспех",
        "description": "Лёгкий и гибкий. +2 к защите.",
        "category": "armor",
        "price": 165,
        "stack_max": 1,
        "consumable": False,
        "equippable": "armor",
        "bonus_def": 2,
    },
    "armor_chain": {
        "name": "Кольчуга",
        "description": "Серьёзная защита. +3 к защите.",
        "category": "armor",
        "price": 380,
        "stack_max": 1,
        "consumable": False,
        "equippable": "armor",
        "bonus_def": 3,
    },
    "armor_plate": {
        "name": "Латы",
        "description": "Тяжёлые латы. +4 к защите.",
        "category": "armor",
        "price": 720,
        "stack_max": 1,
        "consumable": False,
        "equippable": "armor",
        "bonus_def": 4,
    },
    # ── Питомцы (в разработке) ─────────────────────────────────────────────
    "pet_spark_mote": {
        "name": "Искра тумана",
        "description": "Живой огонёк. Механика питомцев в разработке — пока только спутник.",
        "category": "pet",
        "price": 110,
        "stack_max": 1,
        "consumable": False,
        "equippable": "pet",
        "coming_soon": True,
    },
    "pet_void_wisp": {
        "name": "Осколок пустоты",
        "description": "Парящая тень. Бонусы питомцев скоро.",
        "category": "pet",
        "price": 195,
        "stack_max": 1,
        "consumable": False,
        "equippable": "pet",
        "coming_soon": True,
    },
    # ── Прочее ─────────────────────────────────────────────────────────────
    "misc_mist_token": {
        "name": "Жетон тумана",
        "description": "Редкий сувенир из туманных земель. Пока без эффекта.",
        "category": "misc",
        "price": 18,
        "stack_max": 50,
        "consumable": False,
    },
    "misc_lantern_oil": {
        "name": "Масло для фонаря",
        "description": "Пригодится в экспедициях. Скоро: бонус к добыче.",
        "category": "misc",
        "price": 12,
        "stack_max": 99,
        "consumable": False,
        "coming_soon": True,
    },
}


def get_item(item_id: str) -> dict[str, Any] | None:
    return ITEMS.get(item_id)


def shop_item_public(item_id: str) -> dict[str, Any] | None:
    it = ITEMS.get(item_id)
    if not it:
        return None
    return {
        "id": item_id,
        "name": it["name"],
        "description": it["description"],
        "category": it["category"],
        "price": it["price"],
        "stack_max": it.get("stack_max", 99),
        "consumable": it.get("consumable", False),
        "equippable": it.get("equippable"),
        "coming_soon": it.get("coming_soon", False),
    }


def passive_equipment_bonuses(char) -> dict[str, int]:
    """Пассивные бонусы от надетого оружия, брони и питомца (без coming_soon)."""
    out = {"str": 0, "int": 0, "def": 0}
    slots = [
        ("equipped_weapon_id", "weapon"),
        ("equipped_armor_id", "armor"),
        ("equipped_pet_id", "pet"),
    ]
    for attr, _slot in slots:
        iid = getattr(char, attr, None)
        if not iid:
            continue
        it = ITEMS.get(iid)
        if not it or it.get("coming_soon"):
            continue
        out["str"] += int(it.get("bonus_str", 0))
        out["int"] += int(it.get("bonus_int", 0))
        out["def"] += int(it.get("bonus_def", 0))
    return out


def clear_battle_potion_bonuses(char) -> None:
    char.battle_str_bonus = 0
    char.battle_def_bonus = 0
    char.battle_int_bonus = 0
