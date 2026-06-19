from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict

# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "client"  # only client allowed via public endpoint

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)

# ---------- Plans ----------
class PlanBase(BaseModel):
    name: str
    monthly_value: float
    description: str = ""
    active: bool = True

class PlanOut(PlanBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ---------- Artists ----------
class ArtistBase(BaseModel):
    artistic_name: str
    specialties: str = ""
    city: str = ""
    instagram: str = ""
    bio: str = ""
    active: bool = True

class ArtistCreate(ArtistBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class ArtistOut(ArtistBase):
    id: int
    user_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
    avatar_url: str | None = None
    whatsapp: str | None = None
    rating: float = 5.0
    verified: bool = False

# ---------- Client ----------
class ChoosePlanIn(BaseModel):
    plan_id: int

class ChooseArtistIn(BaseModel):
    artist_id: int

class ClientDashboardOut(BaseModel):
    name: str
    plan: Optional[PlanOut] = None
    preferred_artist: Optional[ArtistOut] = None
    lucky_number: Optional[int] = None
    virtual_balance: float
    current_month_paid: bool
    eligible_for_assembly: bool

class ClientAdminOut(BaseModel):
    id: int
    user_id: int
    name: str
    email: EmailStr
    plan: Optional[PlanOut] = None
    preferred_artist: Optional[ArtistOut] = None
    lucky_number: Optional[int] = None
    virtual_balance: float
    is_active: bool

# ---------- Payment ----------
class PaymentRegisterIn(BaseModel):
    client_id: int
    reference_month: int
    reference_year: int

class PaymentOut(BaseModel):
    id: int
    client_id: int
    plan_id: int
    reference_month: int
    reference_year: int
    amount: float
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ---------- Assembly ----------
class AssemblyExecuteIn(BaseModel):
    reference_month: int
    reference_year: int
    exclude_winners: bool = True

class AssemblyParticipantOut(BaseModel):
    client_id: int
    lucky_number: int
    name: str

class AssemblyOut(BaseModel):
    id: int
    reference_month: int
    reference_year: int
    executed_at: datetime
    winner_client_id: Optional[int] = None
    winner_lucky_number: Optional[int] = None
    winner_name: Optional[str] = None
    status: str
    participants: List[AssemblyParticipantOut] = []

# ---------- Appointments ----------
class AppointmentCreateIn(BaseModel):
    description: str
    scheduled_date: Optional[datetime] = None

class AppointmentStatusIn(BaseModel):
    status: str  # scheduled | in_progress | completed

class AppointmentOut(BaseModel):
    id: int
    client_id: int
    client_name: Optional[str] = None
    tattoo_artist_id: int
    artist_name: Optional[str] = None
    assembly_id: Optional[int] = None
    description: str
    scheduled_date: Optional[datetime] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

# ---------- Transactions ----------
class TransactionOut(BaseModel):
    id: int
    client_id: int
    tattoo_artist_id: Optional[int] = None
    type: str
    amount: float
    description: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ---------- Admin dashboard ----------
class AdminDashboardOut(BaseModel):
    total_clients: int
    total_artists: int
    paying_clients: int
    non_paying_clients: int
    assemblies_done: int
    virtual_total: float