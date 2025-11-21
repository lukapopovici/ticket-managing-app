from pydantic import BaseModel
from typing import Optional, List

class EventIn(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    seats: Optional[int] = None

class EventOut(EventIn):
    id: int
    id_owner: int
    class Config:
        from_attributes = True

class PackageIn(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    seats: Optional[int] = None
    event_ids: List[int] = []

class PackageOut(BaseModel):
    id: int
    id_owner: int
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    seats: Optional[int] = None
    class Config:
        from_attributes = True

class TicketIn(BaseModel):
    package_id: Optional[int] = None
    event_id: Optional[int] = None

class TicketOut(BaseModel):
    code: str
    package_id: Optional[int] = None
    event_id: Optional[int] = None

class ValidateTicketIn(BaseModel):
    code: str

class ValidateTicketOut(BaseModel):
    valid: bool
