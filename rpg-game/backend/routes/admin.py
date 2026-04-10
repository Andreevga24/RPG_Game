from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, get_game_db
from models import Monster, City, User, RankEnum
from auth import get_current_user_id
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_admin(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id

class MonsterCreate(BaseModel):
    name: str
    rank: RankEnum
    hp: int
    attack: int
    defense: int
    exp_reward: int
    gold_reward: int
    city_id: int

class CityCreate(BaseModel):
    name: str
    description: str
    min_rank: RankEnum

@router.get("/users")
def list_users(admin=Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in users]

@router.post("/monster")
def create_monster(
    data: MonsterCreate,
    admin=Depends(require_admin),
    game_db: Session = Depends(get_game_db),
):
    m = Monster(**data.model_dump())
    game_db.add(m)
    game_db.commit()
    game_db.refresh(m)
    return {"id": m.id, "name": m.name}

@router.post("/city")
def create_city(
    data: CityCreate,
    admin=Depends(require_admin),
    game_db: Session = Depends(get_game_db),
):
    c = City(**data.model_dump())
    game_db.add(c)
    game_db.commit()
    game_db.refresh(c)
    return {"id": c.id, "name": c.name}

@router.delete("/monster/{monster_id}")
def delete_monster(
    monster_id: int,
    admin=Depends(require_admin),
    game_db: Session = Depends(get_game_db),
):
    m = game_db.query(Monster).filter(Monster.id == monster_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Monster not found")
    game_db.delete(m)
    game_db.commit()
    return {"message": "Deleted"}
