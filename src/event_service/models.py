from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from event_service.db import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    id_owner = Column(Integer, nullable=False)  # owner user id, optional mapping by email in demo
    name = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=True)
    description = Column(String, nullable=True)
    seats = Column(Integer, nullable=True)

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True)
    id_owner = Column(Integer, nullable=False)
    name = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=True)
    description = Column(String, nullable=True)
    seats = Column(Integer, nullable=True)  # seats for the package (<= min of events seats)

class PackageEvent(Base):
    __tablename__ = "package_events"
    package_id = Column(Integer, ForeignKey("packages.id"), primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    __table_args__ = (UniqueConstraint("package_id", "event_id", name="uq_pack_event"),)

class Ticket(Base):
    __tablename__ = "tickets"
    code = Column(String, primary_key=True)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
