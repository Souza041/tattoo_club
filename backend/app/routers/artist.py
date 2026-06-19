from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_artist
from ..models import User, TattooArtist, TattooAppointment, ClientProfile
from ..schemas import AppointmentOut, AppointmentStatusIn

router = APIRouter(prefix="/api/artist", tags=["artist"])

ALLOWED_STATUS = {"scheduled", "in_progress", "completed"}

def _get_artist(db: Session, user: User) -> TattooArtist:
    artist = db.query(TattooArtist).filter(TattooArtist.user_id == user.id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Perfil de tatuador não encontrado")
    return artist

@router.get("/appointments", response_model=List[AppointmentOut])
def appointments(user: User = Depends(require_artist), db: Session = Depends(get_db)):
    artist = _get_artist(db, user)
    rows = db.query(TattooAppointment).filter(TattooAppointment.tattoo_artist_id == artist.id).all()
    out = []
    for r in rows:
        client_user = db.query(User).join(ClientProfile, ClientProfile.user_id == User.id) \
            .filter(ClientProfile.id == r.client_id).first()
        out.append(AppointmentOut(
            id=r.id, client_id=r.client_id,
            client_name=client_user.name if client_user else None,
            tattoo_artist_id=r.tattoo_artist_id,
            artist_name=artist.artistic_name,
            assembly_id=r.assembly_id, description=r.description,
            scheduled_date=r.scheduled_date, status=r.status,
            created_at=r.created_at, completed_at=r.completed_at,
        ))
    return out

@router.patch("/appointments/{appt_id}/status")
def update_status(appt_id: int, data: AppointmentStatusIn,
                  user: User = Depends(require_artist), db: Session = Depends(get_db)):
    artist = _get_artist(db, user)
    appt = db.query(TattooAppointment).filter(TattooAppointment.id == appt_id).first()
    if not appt or appt.tattoo_artist_id != artist.id:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    if data.status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="Status inválido")
    appt.status = data.status
    if data.status == "completed":
        appt.completed_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": appt.status}