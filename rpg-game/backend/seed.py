"""Seed initial game data into game.db only."""
from database import GameSession, game_engine
from models import GameBase, City, Monster, RankEnum

def seed():
    GameBase.metadata.create_all(bind=game_engine)
    db = GameSession()
    if db.query(City).count() > 0:
        print("Already seeded.")
        db.close()
        return

    cities = [
        City(name="Начальный Лес",  description="Тихий лес у подножия гор. Идеальное место для новичков.", min_rank=RankEnum.E),
        City(name="Тёмное Ущелье", description="Опасное ущелье, где обитают сильные монстры.", min_rank=RankEnum.C),
        City(name="Врата Бездны",  description="Место, где открываются Врата в другой мир.", min_rank=RankEnum.A),
    ]
    db.add_all(cities)
    db.flush()

    monsters = [
        # Начальный Лес — E/D/C
        Monster(name="Серый Волк",       rank=RankEnum.E, hp=50,   attack=8,   defense=3,   exp_reward=20,   gold_reward=5,    city_id=cities[0].id),
        Monster(name="Гоблин-разведчик", rank=RankEnum.E, hp=40,   attack=10,  defense=2,   exp_reward=18,   gold_reward=8,    city_id=cities[0].id),
        Monster(name="Ядовитый Паук",    rank=RankEnum.E, hp=35,   attack=7,   defense=1,   exp_reward=15,   gold_reward=4,    city_id=cities[0].id),
        Monster(name="Дикий Кабан",      rank=RankEnum.E, hp=60,   attack=12,  defense=4,   exp_reward=22,   gold_reward=6,    city_id=cities[0].id),
        Monster(name="Лесной Тролль",    rank=RankEnum.D, hp=120,  attack=18,  defense=8,   exp_reward=55,   gold_reward=20,   city_id=cities[0].id),
        Monster(name="Гоблин-шаман",     rank=RankEnum.D, hp=90,   attack=15,  defense=5,   exp_reward=45,   gold_reward=15,   city_id=cities[0].id),
        Monster(name="Костяной Скелет",  rank=RankEnum.D, hp=100,  attack=20,  defense=10,  exp_reward=50,   gold_reward=18,   city_id=cities[0].id),
        Monster(name="Лесная Ведьма",    rank=RankEnum.D, hp=110,  attack=22,  defense=6,   exp_reward=60,   gold_reward=22,   city_id=cities[0].id),
        Monster(name="Огр-страж",        rank=RankEnum.C, hp=200,  attack=28,  defense=15,  exp_reward=100,  gold_reward=40,   city_id=cities[0].id),

        # Тёмное Ущелье — C/B/A
        Monster(name="Каменный Голем",   rank=RankEnum.C, hp=250,  attack=30,  defense=20,  exp_reward=120,  gold_reward=50,   city_id=cities[1].id),
        Monster(name="Пещерный Медведь", rank=RankEnum.C, hp=220,  attack=32,  defense=18,  exp_reward=110,  gold_reward=45,   city_id=cities[1].id),
        Monster(name="Тёмный Маг",       rank=RankEnum.C, hp=180,  attack=40,  defense=12,  exp_reward=130,  gold_reward=55,   city_id=cities[1].id),
        Monster(name="Теневой Дракон",   rank=RankEnum.B, hp=500,  attack=55,  defense=35,  exp_reward=300,  gold_reward=150,  city_id=cities[1].id),
        Monster(name="Рыцарь Смерти",    rank=RankEnum.B, hp=400,  attack=50,  defense=30,  exp_reward=250,  gold_reward=120,  city_id=cities[1].id),
        Monster(name="Горгона",          rank=RankEnum.B, hp=450,  attack=48,  defense=28,  exp_reward=270,  gold_reward=130,  city_id=cities[1].id),
        Monster(name="Химера",           rank=RankEnum.B, hp=520,  attack=60,  defense=32,  exp_reward=320,  gold_reward=160,  city_id=cities[1].id),
        Monster(name="Древний Вампир",   rank=RankEnum.A, hp=900,  attack=85,  defense=50,  exp_reward=600,  gold_reward=300,  city_id=cities[1].id),

        # Врата Бездны — A/S
        Monster(name="Архидемон",        rank=RankEnum.A, hp=1200, attack=100, defense=60,  exp_reward=800,  gold_reward=400,  city_id=cities[2].id),
        Monster(name="Демон Хаоса",      rank=RankEnum.A, hp=1000, attack=95,  defense=55,  exp_reward=700,  gold_reward=350,  city_id=cities[2].id),
        Monster(name="Страж Врат",       rank=RankEnum.A, hp=1100, attack=90,  defense=65,  exp_reward=750,  gold_reward=380,  city_id=cities[2].id),
        Monster(name="Падший Архангел",  rank=RankEnum.A, hp=1300, attack=110, defense=70,  exp_reward=900,  gold_reward=450,  city_id=cities[2].id),
        Monster(name="Король Теней",     rank=RankEnum.S, hp=3000, attack=150, defense=90,  exp_reward=2000, gold_reward=1200, city_id=cities[2].id),
        Monster(name="Дракон Апокалипса",rank=RankEnum.S, hp=4000, attack=180, defense=110, exp_reward=2500, gold_reward=1500, city_id=cities[2].id),
        Monster(name="Владыка Бездны",   rank=RankEnum.S, hp=5000, attack=200, defense=120, exp_reward=3000, gold_reward=2000, city_id=cities[2].id),
        Monster(name="Бог Разрушения",   rank=RankEnum.S, hp=8000, attack=250, defense=150, exp_reward=5000, gold_reward=3000, city_id=cities[2].id),
    ]
    db.add_all(monsters)
    db.commit()
    print("Seeded successfully!")
    db.close()

if __name__ == "__main__":
    seed()
