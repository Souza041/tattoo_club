import random
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import (
    User, ClientProfile, TattooArtist, Plan, Payment, Assembly,
    AssemblyParticipant, TattooAppointment, VirtualTransaction
)
from ..schemas import (
    PlanBase, PlanOut, ArtistCreate, ArtistOut, ClientAdminOut,
    PaymentRegisterIn, PaymentOut, AssemblyExecuteIn, AssemblyOut,
    AssemblyParticipantOut, AppointmentOut, AdminDashboardOut, TransactionOut
)
from ..security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ---------- Dashboard ----------
@router.get("/dashboard", response_model=AdminDashboardOut)
def dashboard(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    total_clients = db.query(ClientProfile).count()
    total_artists = db.query(TattooArtist).count()
    paying_ids = {pid for (pid,) in db.query(Payment.client_id).filter(
        Payment.reference_month == now.month,
        Payment.reference_year == now.year,
        Payment.status == "paid",
    )}
    paying = len(paying_ids)
    non_paying = total_clients - paying
    assemblies_done = db.query(Assembly).count()
    virtual_total = db.query(ClientProfile).with_entities(
        ClientProfile.virtual_balance
    ).all()
    virtual_total = sum(v for (v,) in virtual_total)
    return AdminDashboardOut(
        total_clients=total_clients, total_artists=total_artists,
        paying_clients=paying, non_paying_clients=non_paying,
        assemblies_done=assemblies_done, virtual_total=virtual_total,
    )

# ---------- Clients ----------
@router.get("/clients", response_model=List[ClientAdminOut])
def list_clients(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(ClientProfile).join(User, ClientProfile.user_id == User.id).all()
    out = []
    for c in rows:
        out.append(ClientAdminOut(
            id=c.id, user_id=c.user_id, name=c.user.name, email=c.user.email,
            plan=PlanOut.model_validate(c.plan) if c.plan else None,
            preferred_artist=ArtistOut.model_validate(c.preferred_artist) if c.preferred_artist else None,
            lucky_number=c.lucky_number, virtual_balance=c.virtual_balance,
            is_active=c.is_active,
        ))
    return out

# ---------- Plans CRUD ----------
@router.get("/plans", response_model=List[PlanOut])
def list_plans(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Plan).all()

@router.post("/plans", response_model=PlanOut)
def create_plan(data: PlanBase, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    plan = Plan(**data.model_dump())
    db.add(plan); db.commit(); db.refresh(plan)
    return plan

@router.put("/plans/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, data: PlanBase, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    for k, v in data.model_dump().items():
        setattr(plan, k, v)
    db.commit(); db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    plan.active = False
    db.commit()
    return {"ok": True}

# ---------- Artists CRUD ----------
@router.get("/artists", response_model=List[ArtistOut])
def list_artists_admin(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(TattooArtist).all()

@router.post("/artists", response_model=ArtistOut)
def create_artist(data: ArtistCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user_id = None
    if data.email and data.password and data.name:
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="E-mail já cadastrado")
        u = User(name=data.name, email=data.email,
                 password_hash=hash_password(data.password), role="tattoo_artist")
        db.add(u); db.flush()
        user_id = u.id
    artist = TattooArtist(
        user_id=user_id, artistic_name=data.artistic_name, specialties=data.specialties,
        city=data.city, instagram=data.instagram, bio=data.bio, active=data.active,
    )
    db.add(artist); db.commit(); db.refresh(artist)
    return artist

@router.put("/artists/{artist_id}", response_model=ArtistOut)
def update_artist(artist_id: int, data: ArtistCreate,
                  _: User = Depends(require_admin), db: Session = Depends(get_db)):
    artist = db.query(TattooArtist).filter(TattooArtist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Tatuador não encontrado")
    for k in ("artistic_name", "specialties", "city", "instagram", "bio", "active"):
        setattr(artist, k, getattr(data, k))
    db.commit(); db.refresh(artist)
    return artist

@router.delete("/artists/{artist_id}")
def delete_artist(artist_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    artist = db.query(TattooArtist).filter(TattooArtist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Tatuador não encontrado")
    artist.active = False
    db.commit()
    return {"ok": True}

# ---------- Payments ----------
@router.get("/payments", response_model=List[PaymentOut])
def list_payments(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Payment).order_by(Payment.created_at.desc()).all()

@router.post("/payments", response_model=PaymentOut)
def register_payment(data: PaymentRegisterIn,
                     _: User = Depends(require_admin), db: Session = Depends(get_db)):
    client = db.query(ClientProfile).filter(ClientProfile.id == data.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    if not client.plan_id:
        raise HTTPException(status_code=400, detail="Cliente sem plano ativo")
    dup = db.query(Payment).filter(
        Payment.client_id == client.id,
        Payment.reference_month == data.reference_month,
        Payment.reference_year == data.reference_year,
    ).first()
    if dup:
         raise HTTPException(status_code=400, detail="Pagamento já registrado nesse mês")
    plan = db.query(Plan).filter(Plan.id == client.plan_id).first()
    pay = Payment(
        client_id=client.id, plan_id=plan.id,
        reference_month=data.reference_month, reference_year=data.reference_year,
        amount=plan.monthly_value, status="paid", paid_at=datetime.utcnow(),
    )
    db.add(pay)
    client.virtual_balance = (client.virtual_balance or 0.0) + plan.monthly_value
    db.add(VirtualTransaction(
        client_id=client.id, type="deposit", amount=plan.monthly_value,
        description=f"Mensalidade {data.reference_month:02d}/{data.reference_year}",
    ))
    # TODO_INTEGRATION_PIX: substituir por webhook do gateway
    db.commit(); db.refresh(pay)
    return pay

# ---------- Assemblies ----------
@router.get("/assemblies", response_model=List[AssemblyOut])
def list_assemblies(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    out = []
    for a in db.query(Assembly).order_by(Assembly.executed_at.desc()).all():
        parts = db.query(AssemblyParticipant).filter(AssemblyParticipant.assembly_id == a.id).all()
        participants = []
        for p in parts:
            u = db.query(User).join(ClientProfile, ClientProfile.user_id == User.id) \
                .filter(ClientProfile.id == p.client_id).first()
            participants.append(AssemblyParticipantOut(
                client_id=p.client_id, lucky_number=p.lucky_number,
                name=u.name if u else "?",
            ))
        winner_name = None
        if a.winner_client_id:
            wu = db.query(User).join(ClientProfile, ClientProfile.user_id == User.id) \
                .filter(ClientProfile.id == a.winner_client_id).first()
            winner_name = wu.name if wu else None
        out.append(AssemblyOut(
            id=a.id, reference_month=a.reference_month, reference_year=a.reference_year,
            executed_at=a.executed_at, winner_client_id=a.winner_client_id,
            winner_lucky_number=a.winner_lucky_number, winner_name=winner_name,
            status=a.status, participants=participants,
        ))
    return out

@router.post("/assemblies/execute", response_model=AssemblyOut)
def execute_assembly(data: AssemblyExecuteIn,
                     _: User = Depends(require_admin), db: Session = Depends(get_db)):
    paid_subq = db.query(Payment.client_id).filter(
        Payment.reference_month == data.reference_month,
        Payment.reference_year == data.reference_year,
        Payment.status == "paid",
    ).subquery()
    q = db.query(ClientProfile).filter(
        ClientProfile.id.in_(paid_subq),
        ClientProfile.is_active.is_(True),
        ClientProfile.lucky_number.isnot(None),
    )
    if data.exclude_winners:
        winners = {wid for (wid,) in db.query(Assembly.winner_client_id).filter(Assembly.winner_client_id.isnot(None))}
        if winners:
            q = q.filter(~ClientProfile.id.in_(winners))
    candidates = q.all()
    if not candidates:
        raise HTTPException(status_code=400, detail="Nenhum cliente apto para a assembleia")
    winner = random.choice(candidates)
    assembly = Assembly(
        reference_month=data.reference_month, reference_year=data.reference_year,
        executed_at=datetime.utcnow(),
        winner_client_id=winner.id, winner_lucky_number=winner.lucky_number,
        status="done",
    )
    db.add(assembly); db.flush()
    for c in candidates:
        db.add(AssemblyParticipant(
            assembly_id=assembly.id, client_id=c.id, lucky_number=c.lucky_number,
        ))
    db.commit(); db.refresh(assembly)
    wu = db.query(User).join(ClientProfile, ClientProfile.user_id == User.id) \
        .filter(ClientProfile.id == winner.id).first()
    return AssemblyOut(
        id=assembly.id, reference_month=assembly.reference_month,
        reference_year=assembly.reference_year, executed_at=assembly.executed_at,
        winner_client_id=assembly.winner_client_id,
        winner_lucky_number=assembly.winner_lucky_number,
        winner_name=wu.name if wu else None, status=assembly.status,
        participants=[AssemblyParticipantOut(
            client_id=c.id, lucky_number=c.lucky_number,
            name=c.user.name,
        ) for c in candidates],
    )

# ---------- Appointments ----------
@router.get("/appointments", response_model=List[AppointmentOut])
def list_appointments(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(TattooAppointment).order_by(TattooAppointment.created_at.desc()).all()
    out = []
    for r in rows:
        cu = db.query(User).join(ClientProfile, ClientProfile.user_id == User.id) \
            .filter(ClientProfile.id == r.client_id).first()
        ar = db.query(TattooArtist).filter(TattooArtist.id == r.tattoo_artist_id).first()
        out.append(AppointmentOut(
            id=r.id, client_id=r.client_id, client_name=cu.name if cu else None,
            tattoo_artist_id=r.tattoo_artist_id,
            artist_name=ar.artistic_name if ar else None,
            assembly_id=r.assembly_id, description=r.description,
            scheduled_date=r.scheduled_date, status=r.status,
            created_at=r.created_at, completed_at=r.completed_at,
        ))
    return out

# ---------- Transactions (auditoria) ----------
@router.get("/transactions", response_model=List[TransactionOut])
def list_transactions(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(VirtualTransaction).order_by(VirtualTransaction.created_at.desc()).all()