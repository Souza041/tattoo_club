from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False) # client | tattoo_artist | admin
    created_at = Column(DateTime, default=datetime.utcnow)

    client_profile = relationship("ClientProfile", back_populates="user", uselist=False)
    artist_profile = relationship("TattooArtist", back_populates="user", uselist=False)

class TattooArtist(Base):
    __tablename__ = "tattoo_artists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    artistic_name = Column(String(120), nullable=False)
    specialties = Column(String(255), default="")
    city = Column(String(120), default="")
    instagram = Column(String(120), default="")
    bio = Column(Text, default="")
    active = Column(Boolean, default=True)
    avatar_url = Column(String(500), nullable=True)
    whatsapp = Column(String(30), nullable=True)
    rating = Column(Float, default=5.0)
    verified = Column(Boolean, default=False)

    user = relationship("User", back_populates="artist_profile")

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    monthly_value = Column(Float, nullable=False)
    description = Column(Text, default="")
    active = Column(Boolean, default=True)


class ClientProfile(Base):
      __tablename__ = "client_profiles"
      id = Column(Integer, primary_key=True, index=True)
      user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
      plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
      preferred_artist_id = Column(Integer, ForeignKey("tattoo_artists.id"), nullable=True)
      lucky_number = Column(Integer, unique=True, nullable=True)
      virtual_balance = Column(Float, default=0.0)
      is_active = Column(Boolean, default=True)
      created_at = Column(DateTime, default=datetime.utcnow)

      user = relationship("User", back_populates="client_profile")
      plan = relationship("Plan")
      preferred_artist = relationship("TattooArtist")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    reference_month = Column(Integer, nullable=False)
    reference_year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="paid")  # pending | paid | cancelled
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("client_id", "reference_month", "reference_year", name="uq_payment_month"),
    )


class Assembly(Base):
    __tablename__ = "assemblies"
    id = Column(Integer, primary_key=True, index=True)
    reference_month = Column(Integer, nullable=False)
    reference_year = Column(Integer, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    winner_client_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=True)
    winner_lucky_number = Column(Integer, nullable=True)
    status = Column(String(20), default="done")  # done | cancelled


class AssemblyParticipant(Base):
    __tablename__ = "assembly_participants"
    id = Column(Integer, primary_key=True, index=True)
    assembly_id = Column(Integer, ForeignKey("assemblies.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=False)
    lucky_number = Column(Integer, nullable=False)


class TattooAppointment(Base):
    __tablename__ = "tattoo_appointments"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=False)
    tattoo_artist_id = Column(Integer, ForeignKey("tattoo_artists.id"), nullable=False)
    assembly_id = Column(Integer, ForeignKey("assemblies.id"), nullable=True)
    description = Column(Text, default="")
    scheduled_date = Column(DateTime, nullable=True)
    # requested | scheduled | in_progress | completed | payment_released
    status = Column(String(30), default="requested")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class VirtualTransaction(Base):
    __tablename__ = "virtual_transactions"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("client_profiles.id"), nullable=False)
    tattoo_artist_id = Column(Integer, ForeignKey("tattoo_artists.id"), nullable=True)
    type = Column(String(30), nullable=False)  # deposit | release_to_artist | refund | adjustment
    amount = Column(Float, nullable=False)
    description = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class ArtistPortfolio(Base):
    __tablename__ = "artist_portfolio"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("tattoo_artists.id"))
    image_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)