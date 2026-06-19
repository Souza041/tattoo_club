from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Plan, TattooArtist
from ..schemas import PlanOut, ArtistOut

router = APIRouter(prefix="/api", tags=["public"])

@router.get("/plans", response_model=List[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).filter(Plan.active.is_(True)).order_by(Plan.monthly_value).all()

@router.get("/artists", response_model=List[ArtistOut])
def list_artists(db: Session = Depends(get_db)):
    return db.query(TattooArtist).filter(TattooArtist.active.is_(True)).order_by(TattooArtist.artistic_name).all()