import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from event_service.db import Base, engine, SessionLocal
from event_service import models, schemas
from common.deps import get_current_user, require_role

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Event Service")

origins = os.getenv("CORS_ORIGINS", "*")
allow_origins = ["*"] if origins == "*" else [o.strip() for o in origins.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allow_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utilities
def ensure_owner(user: dict) -> int:
    # ???????
    return abs(hash(user["sub"])) % (10**6)

# Events
@app.get("/events", response_model=List[schemas.EventOut])
def list_events(q: Optional[str] = None, loc: Optional[str] = None,
                minSeats: Optional[int] = None, maxSeats: Optional[int] = None,
                db: Session = Depends(get_db), user=Depends(get_current_user)):
    query = db.query(models.Event)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(func.lower(models.Event.name).like(like))
    if loc:
        like = f"%{loc.lower()}%"
        query = query.filter(func.lower(models.Event.location).like(like))
    if minSeats is not None:
        query = query.filter((models.Event.seats >= minSeats) | (models.Event.seats.is_(None)))
    if maxSeats is not None:
        query = query.filter((models.Event.seats <= maxSeats) | (models.Event.seats.is_(None)))
    # Filtrare după numărul de bilete disponibile
    available_tickets: Optional[int] = Query(None, ge=0)
    page: int = Query(1, ge=1)
    items_per_page: int = Query(10, ge=1)
    if available_tickets is not None:
        query = query.outerjoin(models.Ticket, models.Event.id == models.Ticket.event_id)
        query = query.group_by(models.Event.id)
        query = query.having((models.Event.seats - func.count(models.Ticket.code)) >= available_tickets)
    # paginare
    return query.offset((page - 1) * items_per_page).limit(items_per_page).all()

@app.post("/events", response_model=schemas.EventOut)
def create_event(body: schemas.EventIn, db: Session = Depends(get_db), user=Depends(require_role("owner-event"))):
    owner_id = ensure_owner(user)
    ev = models.Event(id_owner=owner_id, name=body.name, location=body.location, description=body.description, seats=body.seats)
    db.add(ev)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Event name must be unique")
    db.refresh(ev)
    return ev

@app.put("/events/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, body: schemas.EventIn, db: Session = Depends(get_db), user=Depends(require_role("owner-event"))):
    owner_id = ensure_owner(user)
    ev = db.query(models.Event).get(event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if ev.id_owner != owner_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # Rule: seats cannot be changed after first ticket sold
    ticket_exists = db.query(models.Ticket).filter(models.Ticket.event_id == event_id).first()
    if ticket_exists and body.seats != ev.seats:
        raise HTTPException(status_code=400, detail="Cannot modify seats after tickets sold")
    for k, v in body.dict().items():
        setattr(ev, k, v)
    db.commit()
    db.refresh(ev)
    return ev

# Packages
@app.post("/packages", response_model=schemas.PackageOut)
def create_package(body: schemas.PackageIn, db: Session = Depends(get_db), user=Depends(require_role("owner-event"))):
    owner_id = ensure_owner(user)
    # compute min seats
    if body.event_ids:
        events = db.query(models.Event).filter(models.Event.id.in_(body.event_ids)).all()
        if not events or len(events) != len(body.event_ids):
            raise HTTPException(status_code=400, detail="Some events not found")
        min_seats = min([e.seats or 0 for e in events]) if any(e.seats is not None for e in events) else None
        if body.seats is not None and min_seats is not None and body.seats > min_seats:
            raise HTTPException(status_code=400, detail="Package seats must be <= min seats of events")
    pkg = models.Package(id_owner=owner_id, name=body.name, location=body.location, description=body.description, seats=body.seats)
    db.add(pkg)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Package name must be unique")
    db.refresh(pkg)
    # join
    for eid in body.event_ids:
        db.add(models.PackageEvent(package_id=pkg.id, event_id=eid))
    db.commit()
    return pkg

# Tickets
@app.post("/tickets", response_model=schemas.TicketOut)
def create_ticket(body: schemas.TicketIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # simple availability check: count existing tickets for event/package and compare with seats
    if not body.event_id and not body.package_id:
        raise HTTPException(status_code=400, detail="Provide event_id or package_id")
    if body.event_id:
        ev = db.query(models.Event).get(body.event_id)
        if not ev:
            raise HTTPException(status_code=404, detail="Event not found")
        if ev.seats is not None:
            sold = db.query(models.Ticket).filter(models.Ticket.event_id == body.event_id).count()
            if sold >= ev.seats:
                raise HTTPException(status_code=400, detail="Sold out")
    if body.package_id:
        pkg = db.query(models.Package).get(body.package_id)
        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")
        if pkg.seats is not None:
            sold = db.query(models.Ticket).filter(models.Ticket.package_id == body.package_id).count()
            if sold >= pkg.seats:
                raise HTTPException(status_code=400, detail="Sold out")
    code = uuid.uuid4().hex[:12]
    t = models.Ticket(code=code, package_id=body.package_id, event_id=body.event_id)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"code": t.code, "package_id": t.package_id, "event_id": t.event_id}

@app.post("/validate/ticket", response_model=schemas.ValidateTicketOut)
def validate_ticket(body: schemas.ValidateTicketIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    exists = db.query(models.Ticket).get(body.code)
    return {"valid": exists is not None}

# Relații: eveniment <-> pachet
@app.get("/events/{event_id}/event-packets", response_model=List[schemas.PackageOut])
def get_event_packages(event_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    packages = db.query(models.Package).join(models.PackageEvent).filter(models.PackageEvent.event_id == event_id).all()
    return packages

@app.get("/event-packets/{package_id}/events", response_model=List[schemas.EventOut])
def get_package_events(package_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    events = db.query(models.Event).join(models.PackageEvent).filter(models.PackageEvent.package_id == package_id).all()
    return events

# Relații: bilete pentru eveniment/pachet
@app.get("/events/{event_id}/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_event_ticket(event_id: int, ticket_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ticket = db.query(models.Ticket).filter(models.Ticket.event_id == event_id, models.Ticket.code == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.get("/event-packets/{package_id}/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_package_ticket(package_id: int, ticket_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ticket = db.query(models.Ticket).filter(models.Ticket.package_id == package_id, models.Ticket.code == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

# Paginare și filtrare avansată pentru pachete
@app.get("/event-packets", response_model=List[schemas.PackageOut])
def list_event_packets(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1),
    available_tickets: Optional[int] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = db.query(models.Package)
    if type:
        like = f"%{type.lower()}%"
        query = query.filter(func.lower(models.Package.description).like(like))
    if available_tickets is not None:
        # numărul de bilete disponibile = seats - bilete vândute
        query = query.outerjoin(models.Ticket, models.Package.id == models.Ticket.package_id)
        query = query.group_by(models.Package.id)
        query = query.having((models.Package.seats - func.count(models.Ticket.code)) >= available_tickets)
    # paginare
    return query.offset((page - 1) * items_per_page).limit(items_per_page).all()

@app.get("/health")
def health():
    return {"ok": True}
