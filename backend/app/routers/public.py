from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Plan, TattooArtist, ArtistAvailability
from ..schemas import PlanOut, ArtistOut

router = APIRouter(prefix="/api", tags=["public"])

@router.get("/plans", response_model=List[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).filter(Plan.active.is_(True)).order_by(Plan.monthly_value).all()

@router.get("/artists", response_model=List[ArtistOut])
def list_artists(db: Session = Depends(get_db)):
    return db.query(TattooArtist).filter(TattooArtist.active.is_(True)).order_by(TattooArtist.artistic_name).all()

@router.get("/artists/{artist_id}/availability")
def artist_availability(artist_id: int, db: Session = Depends(get_db)):
    return db.query(ArtistAvailability).filter(
        ArtistAvailability.artist_id == artist_id,
        ArtistAvailability.is_booked.is_(False),
    ).order_by(ArtistAvailability.available_at.asc()).all()