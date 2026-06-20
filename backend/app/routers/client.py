from datetime import datetime, date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_client
from ..models import (
    User, ClientProfile, Plan, TattooArtist, Payment, Assembly,
    TattooAppointment, VirtualTransaction, ArtistAvailability, TattooSession
)
from ..schemas import (
    ChoosePlanIn, ChooseArtistIn, ClientDashboardOut,
    PaymentOut, AssemblyOut, AssemblyParticipantOut,
    AppointmentCreateIn, AppointmentOut, PlanOut, ArtistOut,
    TransactionOut, TattooSessionOut
)

router = APIRouter(prefix="/api/client", tags=["client"])

def _get_profile(db: Session, user: User) -> ClientProfile:
    profile = db.query(ClientProfile).filter(ClientProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de cliente não encontrado")
    return profile

def _generate_lucky_number(db: Session) -> int:
    used = {n for (n,) in db.query(ClientProfile.lucky_number).filter(ClientProfile.lucky_number.isnot(None))}
    for i in range(1, 10000):
        if i not in used:
            return i
    raise HTTPException(status_code=500, detail="Sem números da sorte disponíveis")

def _is_paid_this_month(db: Session, client_id: int) -> bool:
    now = datetime.utcnow()
    return db.query(Payment).filter(
        Payment.client_id == client_id,
        Payment.reference_month == now.month,
        Payment.reference_year == now.year,
        Payment.status == "paid",
    ).first() is not None

@router.get("/dashboard", response_model=ClientDashboardOut)
def dashboard(user: User = Depends(require_client), db: Session = Depends(get_db)):
    profile = _get_profile(db, user)
    paid = _is_paid_this_month(db, profile.id)
    return ClientDashboardOut(
        name=user.name,
        plan=PlanOut.model_validate(profile.plan) if profile.plan else None,
        preferred_artist=ArtistOut.model_validate(profile.preferred_artist) if profile.preferred_artist else None,
        lucky_number=profile.lucky_number,
        virtual_balance=profile.virtual_balance,
        current_month_paid=paid,
        eligible_for_assembly=paid and profile.plan_id is not None,
    )

@router.post("/plan")
def choose_plan(data: ChoosePlanIn, user: User = Depends(require_client), db: Session = Depends(get_db)):
    profile = _get_profile(db, user)
    plan = db.query(Plan).filter(Plan.id == data.plan_id, Plan.active.is_(True)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    profile.plan_id = plan.id
    if profile.lucky_number is None:
        profile.lucky_number = _generate_lucky_number(db)
    db.commit()
    return {"ok": True, "lucky_number": profile.lucky_number}

@router.post("/artist")
def choose_artist(data: ChooseArtistIn, user: User = Depends(require_client), db: Session = Depends(get_db)):
    profile = _get_profile(db, user)
    artist = db.query(TattooArtist).filter(TattooArtist.id == data.artist_id, TattooArtist.active.is_(True)).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Tatuador não encontrado")
    profile.preferred_artist_id = artist.id
    db.commit()
    return {"ok": True}

@router.get("/payments", response_model=List[PaymentOut])
def my_payments(user: User = Depends(require_client), db: Session = Depends(get_db)):
    profile = _get_profile(db, user)
    return db.query(Payment).filter(Payment.client_id == profile.id).order_by(
        Payment.reference_year.desc(), Payment.reference_month.desc()
    ).all()

@router.get("/assemblies", response_model=List[AssemblyOut])
def assemblies(db: Session = Depends(get_db), user: User = Depends(require_client)):
    out = []
    for a in db.query(Assembly).order_by(Assembly.executed_at.desc()).all():
        winner_name = None
        if a.winner_client_id:
            w = db.query(User).join(ClientProfile, ClientProfile.user_id == User.id) \
                .filter(ClientProfile.id == a.winner_client_id).first()
            winner_name = w.name if w else None
        out.append(AssemblyOut(
            id=a.id, reference_month=a.reference_month, reference_year=a.reference_year,
            executed_at=a.executed_at, winner_client_id=a.winner_client_id,
            winner_lucky_number=a.winner_lucky_number, winner_name=winner_name,
            status=a.status, participants=[],
        ))
    return out

@router.get("/appointments", response_model=List[AppointmentOut])
def my_appointments(user: User = Depends(require_client), db: Session = Depends(get_db)):
    profile = _get_profile(db, user)
    rows = db.query(TattooAppointment).filter(TattooAppointment.client_id == profile.id).all()
    out = []
    for r in rows:
        artist = db.query(TattooArtist).filter(TattooArtist.id == r.tattoo_artist_id).first()
        out.append(AppointmentOut(
            id=r.id, client_id=r.client_id, client_name=user.name,
            tattoo_artist_id=r.tattoo_artist_id,
            artist_name=artist.artistic_name if artist else None,
            assembly_id=r.assembly_id, description=r.description,
            scheduled_date=r.scheduled_date, status=r.status,
            created_at=r.created_at, completed_at=r.completed_at,
        ))
    return out

@router.post("/appointments", response_model=AppointmentOut)
def request_appointment(
    data: AppointmentCreateIn,
    user: User = Depends(require_client),
    db: Session = Depends(get_db),
):
    profile = _get_profile(db, user)

    if not profile.preferred_artist_id:
        raise HTTPException(status_code=400, detail="Escolha um tatuador antes")

    won = db.query(Assembly).filter(
        Assembly.winner_client_id == profile.id
    ).order_by(Assembly.executed_at.desc()).first()

    if not won:
        raise HTTPException(status_code=403, detail="Você ainda não foi contemplado em uma assembleia")

    if data.total_sessions < 1:
        raise HTTPException(status_code=400, detail="Informe ao menos 1 sessão")

    if len(data.sessions) != data.total_sessions:
        raise HTTPException(status_code=400, detail="Quantidade de horários diferente da quantidade de sessões")

    already = db.query(TattooAppointment).filter(
        TattooAppointment.client_id == profile.id,
        TattooAppointment.assembly_id == won.id,
    ).first()

    if already:
        raise HTTPException(status_code=400, detail="Já existe agendamento para sua contemplação")

    appt = TattooAppointment(
        client_id=profile.id,
        tattoo_artist_id=profile.preferred_artist_id,
        assembly_id=won.id,
        description=data.description,
        scheduled_date=data.sessions[0].scheduled_start,
        status="requested",
    )

    db.add(appt)
    db.flush()

    artist = db.query(TattooArtist).filter(
        TattooArtist.id == profile.preferred_artist_id
    ).first()

    duration = artist.default_session_hours or 2.0

    for idx, session in enumerate(data.sessions, start=1):
        start = session.scheduled_start
        end = start + timedelta(hours=duration)

        conflict = db.query(TattooSession).filter(
            TattooSession.tattoo_artist_id == profile.preferred_artist_id,
            TattooSession.scheduled_start < end,
            TattooSession.scheduled_end > start,
            TattooSession.status != "cancelled",
        ).first()

        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Conflito de agenda na sessão {idx}"
            )

        db.add(TattooSession(
            appointment_id=appt.id,
            tattoo_artist_id=profile.preferred_artist_id,
            client_id=profile.id,
            session_number=idx,
            duration_hours=duration,
            scheduled_start=start,
            scheduled_end=end,
            status="scheduled",
        ))

    db.commit()
    db.refresh(appt)

    artist = db.query(TattooArtist).filter(TattooArtist.id == appt.tattoo_artist_id).first()

    return AppointmentOut(
        id=appt.id,
        client_id=appt.client_id,
        client_name=user.name,
        tattoo_artist_id=appt.tattoo_artist_id,
        artist_name=artist.artistic_name if artist else None,
        assembly_id=appt.assembly_id,
        description=appt.description,
        scheduled_date=appt.scheduled_date,
        status=appt.status,
        created_at=appt.created_at,
        completed_at=appt.completed_at,
    )

@router.post("/appointments/{appt_id}/release")
def release_payment(appt_id: int, user: User = Depends(require_client), db: Session = Depends(get_db)):
    profile = _get_profile(db, user)
    appt = db.query(TattooAppointment).filter(TattooAppointment.id == appt_id).first()
    if not appt or appt.client_id != profile.id:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    if appt.status != "completed":
        raise HTTPException(status_code=400, detail="Só é possível liberar após o serviço ser concluído")
    if profile.virtual_balance <= 0:
        raise HTTPException(status_code=400, detail="Sem saldo virtual para liberar")

    amount = profile.virtual_balance
    profile.virtual_balance = 0.0
    appt.status = "payment_released"
    db.add(VirtualTransaction(
        client_id=profile.id,
        tattoo_artist_id=appt.tattoo_artist_id,
        type="release_to_artist",
        amount=amount,
        description=f"Liberação para tatuador (appt {appt.id})",
    ))
    # TODO_INTEGRATION_PIX: aqui dispara transferência real ao tatuador
    db.commit()
    return {"ok": True, "released": amount}

@router.get("/transactions", response_model=List[TransactionOut])
def my_transactions(
    user: User = Depends(require_client),
    db: Session = Depends(get_db)
):
    profile = _get_profile(db, user)

    return db.query(VirtualTransaction)\
        .filter(VirtualTransaction.client_id == profile.id)\
        .order_by(VirtualTransaction.created_at.desc())\
        .all()

@router.get("/next-assembly")
def next_assembly(user: User = Depends(require_client), db: Session = Depends(get_db)):
    profile = _get_profile(db, user)

    today = date.today()

    if today.month == 12:
        next_month = 1
        next_year = today.year + 1
    else:
        next_month = today.month + 1
        next_year = today.year

    scheduled = date(next_year, next_month, 15)

    paid = db.query(Payment).filter(
        Payment.client_id == profile.id,
        Payment.reference_month == today.month,
        Payment.reference_year == today.year,
        Payment.status == "paid",
    ).first() is not None

    return {
        "reference_month": next_month,
        "reference_year": next_year,
        "scheduled_date": scheduled.isoformat(),
        "label": scheduled.strftime("%d/%m/%Y"),
        "eligible": paid and profile.plan_id is not None,
    }
    
@router.get("/appointments/{appt_id}/sessions", response_model=List[TattooSessionOut])
def appointment_sessions(
    appt_id: int,
    user: User = Depends(require_client),
    db: Session = Depends(get_db)
):
    profile = _get_profile(db, user)

    appt = db.query(TattooAppointment).filter(
        TattooAppointment.id == appt_id,
        TattooAppointment.client_id == profile.id,
    ).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    return db.query(TattooSession).filter(
        TattooSession.appointment_id == appt.id
    ).order_by(TattooSession.session_number.asc()).all()