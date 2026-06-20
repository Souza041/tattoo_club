from datetime import datetime, timedelta, time
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_artist
from ..models import User, TattooArtist, TattooAppointment, ClientProfile, ArtistAvailability, ArtistSchedule
from ..schemas import AppointmentOut, AppointmentStatusIn, AvailabilityCreateIn, AvailabilityOut, ArtistScheduleIn, ArtistScheduleOut, ArtistScheduleSaveIn

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

@router.get("/availability", response_model=List[AvailabilityOut])
def my_availability(user: User = Depends(require_artist), db: Session = Depends(get_db)):
    artist = _get_artist(db, user)
    return db.query(ArtistAvailability).filter(
        ArtistAvailability.artist_id == artist.id
    ).order_by(ArtistAvailability.available_at.asc()).all()


@router.post("/availability", response_model=AvailabilityOut)
def add_availability(
    data: AvailabilityCreateIn,
    user: User = Depends(require_artist),
    db: Session = Depends(get_db)
):
    artist = _get_artist(db, user)

    slot = ArtistAvailability(
        artist_id=artist.id,
        available_at=data.available_at,
        is_booked=False,
    )

    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

@router.get("/schedule", response_model=List[ArtistScheduleOut])
def my_schedule(
    user: User = Depends(require_artist),
    db: Session = Depends(get_db)
):
    artist = _get_artist(db, user)

    return db.query(ArtistSchedule).filter(
        ArtistSchedule.artist_id == artist.id
    ).order_by(ArtistSchedule.weekday.asc()).all()


@router.post("/schedule", response_model=List[ArtistScheduleOut])
def save_schedule(
    data: ArtistScheduleSaveIn,
    user: User = Depends(require_artist),
    db: Session = Depends(get_db)
):
    artist = _get_artist(db, user)

    if data.default_session_hours <= 0:
        raise HTTPException(status_code=400, detail="Duração da sessão inválida")

    artist.default_session_hours = data.default_session_hours

    db.query(ArtistSchedule).filter(
        ArtistSchedule.artist_id == artist.id
    ).delete()

    for row in data.schedule:
        if row.weekday < 0 or row.weekday > 6:
            raise HTTPException(status_code=400, detail="Dia da semana inválido")

        if row.start_hour >= row.end_hour:
            raise HTTPException(status_code=400, detail="Horário inicial deve ser menor que o final")

        db.add(ArtistSchedule(
            artist_id=artist.id,
            weekday=row.weekday,
            start_hour=row.start_hour,
            end_hour=row.end_hour,
            active=row.active,
        ))

    db.flush()
    _generate_slots_for_artist(db, artist, days_ahead=60)
    db.commit()

    return db.query(ArtistSchedule).filter(
        ArtistSchedule.artist_id == artist.id
    ).order_by(ArtistSchedule.weekday.asc()).all()
    
def _parse_hour(value: str) -> time:
    try:
        h, m = value.split(":")
        return time(hour=int(h), minute=int(m))
    except Exception:
        raise HTTPException(status_code=400, detail="Horário inválido. Use HH:MM")


def _generate_slots_for_artist(db: Session, artist: TattooArtist, days_ahead: int = 60):
    duration_hours = artist.default_session_hours or 2.0
    duration = timedelta(hours=duration_hours)

    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days_ahead)

    schedules = db.query(ArtistSchedule).filter(
        ArtistSchedule.artist_id == artist.id,
        ArtistSchedule.active.is_(True),
    ).all()

    # Limpa slots futuros ainda não reservados para regerar sem duplicar
    db.query(ArtistAvailability).filter(
        ArtistAvailability.artist_id == artist.id,
        ArtistAvailability.is_booked.is_(False),
        ArtistAvailability.available_at >= datetime.combine(today, time.min),
    ).delete()

    current = today

    while current <= end_date:
        weekday = current.weekday()

        day_schedules = [s for s in schedules if s.weekday == weekday]

        for s in day_schedules:
            start_t = _parse_hour(s.start_hour)
            end_t = _parse_hour(s.end_hour)

            slot_start = datetime.combine(current, start_t)
            day_end = datetime.combine(current, end_t)

            while slot_start + duration <= day_end:
                db.add(ArtistAvailability(
                    artist_id=artist.id,
                    available_at=slot_start,
                    is_booked=False,
                ))

                slot_start += duration

        current += timedelta(days=1)