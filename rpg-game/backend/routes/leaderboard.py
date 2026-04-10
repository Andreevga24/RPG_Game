from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Character, User
from schemas import LeaderboardEntry
from auth import get_current_user_id
from typing import Optional

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])

@router.get("", response_model=list[LeaderboardEntry])
def get_leaderboard(
    rank_filter: Optional[str] = Query(None),
    class_filter: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    query = db.query(Character, User).join(User, Character.user_id == User.id)
    if rank_filter:
        query = query.filter(Character.rank == rank_filter)
    if class_filter:
        query = query.filter(Character.char_class == class_filter)
    results = query.order_by(Character.f1_points.desc()).limit(100).all()
    entries = []
    for i, (char, user) in enumerate(results):
        entries.append(LeaderboardEntry(
            rank_position=i + 1,
            username=user.username,
            rank=char.rank.value,
            char_class=char.char_class.value,
            f1_points=char.f1_points
        ))
    return entries
