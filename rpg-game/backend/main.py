from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import players_engine, game_engine, migrate_players_schema
from models import PlayersBase, GameBase
from routes import auth, character, city, fight, raid, leaderboard, admin, shop_inventory
from routes.shop_inventory import shop_catalog_response
import os

# Create tables in their respective databases
PlayersBase.metadata.create_all(bind=players_engine)
migrate_players_schema()
GameBase.metadata.create_all(bind=game_engine)

app = FastAPI(title="Новые приключения фанфиков API", version="2.0.0")

_cors_default = (
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:3001,http://127.0.0.1:3001"
)
_cors_origins_raw = os.getenv("CORS_ORIGINS", _cors_default)
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
_allow_all_origins = any(o == "*" for o in _cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all_origins else _cors_origins,
    # If allow_origins=["*"], credentials are not allowed by browsers and are unsafe for prod.
    allow_credentials=False if _allow_all_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(character.router)


@app.get("/api/shop", tags=["shop"])
def list_shop_catalog():
    """Каталог товаров; дублирует логику shop_inventory, чтобы маршрут всегда был на app."""
    return shop_catalog_response()


app.include_router(shop_inventory.router)
app.include_router(city.router)
app.include_router(fight.router)
app.include_router(raid.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "message": "Новые приключения фанфиков API is running",
        "shop_enabled": True,
    }
