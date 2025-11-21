from pydantic import BaseModel, EmailStr
from typing import Optional, List, Literal, Dict

class Social(BaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None

class Ticket(BaseModel):
    cod: str
    tip: Literal["eveniment", "pachet"]
    eveniment: Optional[Dict] = None
    pachet: Optional[Dict] = None

class ClientCreate(BaseModel):
    email: EmailStr
    prenume: Optional[str] = None
    nume: Optional[str] = None
    public: bool = True
    social: Optional[Social] = None

class ClientOut(ClientCreate):
    id: str

class AddTicketIn(BaseModel):
    cod: str
    tip: Literal["eveniment", "pachet"]
    eveniment_nume: Optional[str] = None
    eveniment_locatie: Optional[str] = None
    pachet_nume: Optional[str] = None
