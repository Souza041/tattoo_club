from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from .models import User, Plan, TattooArtist, ClientProfile
from .security import hash_password
from .config import settings

def _ensure_admin(db: Session):
    if db.query(User).filter(User.email == settings.ADMIN_EMAIL).first():
        return
    admin = User(
        name="Administrador",
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role="admin",
    )
    db.add(admin)

def _ensure_plans(db: Session):
    if db.query(Plan).count() > 0:
        return
    db.add_all([
        Plan(name="Plano Fine Line", monthly_value=80.0,
             description="Reserve para tattoos pequenas e delicadas."),
        Plan(name="Plano Black & Grey", monthly_value=150.0,
             description="Para peças médias em preto e cinza."),
        Plan(name="Plano Realismo", monthly_value=250.0,
             description="Para peças grandes e detalhadas."),
    ])

def _ensure_artists(db: Session):
    if db.query(TattooArtist).count() > 0:
        return
    artists = [
        ("Marina Ink", "marina@tattooclub.com", "Fine line, minimalista", "São Paulo", "@marina.ink"),
        ("Caio Black", "caio@tattooclub.com", "Black & grey, realismo", "Rio de Janeiro", "@caio.black"),
        ("Lara Color", "lara@tattooclub.com", "Aquarela, colorido", "Curitiba", "@lara.color"),
    ]
    for name, email, spec, city, ig in artists:
        u = User(name=name, email=email, password_hash=hash_password("artist123"), role="tattoo_artist")
        db.add(u)
        db.flush()
        db.add(TattooArtist(
            user_id=u.id, artistic_name=name, specialties=spec, city=city,
            instagram=ig, bio=f"Artista {name} disponível no Tattoo Club.", active=True
        ))

def _ensure_test_clients(db: Session):
    if db.query(User).filter(User.role == "client").count() > 0:
        return
    for i in range(1, 4):
        u = User(
            name=f"Cliente Teste {i}",
            email=f"cliente{i}@tattooclub.com",
            password_hash=hash_password("cliente123"),
            role="client",
        )
        db.add(u)
        db.flush()
        db.add(ClientProfile(user_id=u.id, virtual_balance=0.0, is_active=True))

def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _ensure_admin(db)
        _ensure_plans(db)
        _ensure_artists(db)
        _ensure_test_clients(db)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
    print("Seed executado.")