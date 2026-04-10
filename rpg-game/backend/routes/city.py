from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_game_db
from models import City
from schemas import CityOut
from auth import get_current_user_id

router = APIRouter(prefix="/api/city", tags=["city"])

@router.get("", response_model=list[CityOut])
def get_cities(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_game_db)):
    return db.query(City).all()

@router.get("/{city_id}", response_model=CityOut)
def get_city(city_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_game_db)):
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="City not found")
    return city
