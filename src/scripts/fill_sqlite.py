import sys
sys.path.append('..')
from event_service.db import SessionLocal, Base, engine
from event_service.models import Event, Package, PackageEvent, Ticket

Base.metadata.create_all(bind=engine)
db = SessionLocal()

events = [
    Event(id_owner=1, name="Concert Rock", location="Sala Polivalenta", description="Concert de rock", seats=100),
    Event(id_owner=2, name="Teatru Clasic", location="Teatrul National", description="Piesa de teatru", seats=80),
    Event(id_owner=1, name="Conferinta IT", location="Hotel Central", description="Conferinta IT", seats=150)
]
for ev in events:
    db.add(ev)
db.commit()

packages = [
    Package(id_owner=1, name="Pachet Cultura", location="Oras", description="Teatru si conferinta", seats=70),
    Package(id_owner=2, name="Pachet Muzica", location="Oras", description="Concert", seats=90)
]
for pkg in packages:
    db.add(pkg)
db.commit()

# Join events to packages
joins = [
    PackageEvent(package_id=packages[0].id, event_id=events[1].id),
    PackageEvent(package_id=packages[0].id, event_id=events[2].id),
    PackageEvent(package_id=packages[1].id, event_id=events[0].id)
]
for j in joins:
    db.add(j)
db.commit()

tickets = [
    Ticket(code="TICKET1", event_id=events[0].id),
    Ticket(code="TICKET2", package_id=packages[0].id),
    Ticket(code="TICKET3", event_id=events[2].id)
]
for t in tickets:
    db.add(t)
db.commit()
db.close()
