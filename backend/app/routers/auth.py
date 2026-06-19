from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, ClientProfile
from ..schemas import UserCreate, TokenOut, UserOut
from ..security import hash_password, verify_password, create_access_token
from ..deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if data.role != "client":
        raise HTTPException(status_code=400, detail="Cadastro público apenas para clientes")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    user = User(
        name=data.name, email=data.email,
        password_hash=hash_password(data.password), role="client",
    )
    db.add(user)
    db.flush()
    db.add(ClientProfile(user_id=user.id, virtual_balance=0.0, is_active=True))
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenOut(access_token=token, role=user.role, user_id=user.id, name=user.name)

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenOut(access_token=token, role=user.role, user_id=user.id, name=user.name)

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user