import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
import httpx
from client_service.db import clients
from client_service.schemas import ClientCreate, ClientOut, AddTicketIn
from common.deps import get_current_user

EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "http://localhost:8001")

app = FastAPI(title="Client Service")

#HATEOAS-ul
# Informare client despre creare/actualizare profil + unde sunt biletele
@app.get("/clients")
async def info_clients():
    return {
        "message": "Acest serviciu permite gestiunea profilului și biletelor tale pentru evenimente/pachete.",
        "links": [
            {"rel": "create-profile", "href": "/clients/me", "method": "POST"},
            {"rel": "read-profile", "href": "/clients/me", "method": "GET"},
            {"rel": "update-profile", "href": "/clients/me", "method": "PUT"},
            {"rel": "list-tickets", "href": "/clients/me/tickets", "method": "GET"},
            {"rel": "add-ticket", "href": "/clients/me/tickets", "method": "POST"}
        ]
    }

def oid_str(oid):
    return str(oid)

@app.post("/clients/me")
async def create_or_get_me(body: ClientCreate, user=Depends(get_current_user)):
    # user.sub is the email from token; ensure match or admin role
    if user["role"] != "admin" and user["sub"] != body.email:
        raise HTTPException(status_code=403, detail="Email mismatch")
    doc = await clients.find_one({"email": body.email})
    if doc:
        return {"id": oid_str(doc["_id"]), **{k: doc.get(k) for k in ["email","prenume","nume","public","social"]}}
    res = await clients.insert_one(body.model_dump())
    created = await clients.find_one({"_id": res.inserted_id})
    return {"id": oid_str(created["_id"]), **{k: created.get(k) for k in ["email","prenume","nume","public","social"]}}

@app.get("/clients/me")
async def get_me(user=Depends(get_current_user)):
    doc = await clients.find_one({"email": user["sub"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"id": oid_str(doc["_id"]), **{k: doc.get(k) for k in ["email","prenume","nume","public","social"]}}

@app.put("/clients/me")
async def update_me(body: ClientCreate, user=Depends(get_current_user)):
    if user["sub"] != body.email:
        raise HTTPException(status_code=403, detail="Email mismatch")
    await clients.update_one({"email": body.email}, {"$set": body.model_dump()}, upsert=True)
    doc = await clients.find_one({"email": body.email})
    return {"id": oid_str(doc["_id"]), **{k: doc.get(k) for k in ["email","prenume","nume","public","social"]}}

@app.get("/clients/me/tickets")
async def my_tickets(user=Depends(get_current_user)):
    doc = await clients.find_one({"email": user["sub"]})
    if not doc:
        return {"bilete": []}
    return {"bilete": doc.get("bilete", [])}

@app.post("/clients/me/tickets")
async def add_ticket(body: AddTicketIn, user=Depends(get_current_user)):
    # Chain validation with Event Service
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{EVENT_SERVICE_URL}/validate/ticket", json={"code": body.cod}, headers={"Authorization": f"Bearer dummy"})
            r.raise_for_status()
        except Exception:
            raise HTTPException(status_code=502, detail="Event service unavailable")
    valid = r.json().get("valid", False)
    if not valid:
        raise HTTPException(status_code=400, detail="Ticket invalid")
    ticket_doc = {
        "cod": body.cod,
        "tip": body.tip,
        "eveniment": {"nume": body.eveniment_nume, "locatie": body.eveniment_locatie} if body.tip == "eveniment" else None,
        "pachet": {"nume": body.pachet_nume} if body.tip == "pachet" else None
    }
    await clients.update_one({"email": user["sub"]}, {"$push": {"bilete": ticket_doc}}, upsert=True)
    return JSONResponse({"added": True, "cod": body.cod})

# Detalii bilet: re-validează și aduce info eveniment/pachet
@app.get("/clients/me/tickets/{code}/details")
async def ticket_details(code: str, user=Depends(get_current_user)):
    # Caută biletul la client
    doc = await clients.find_one({"email": user["sub"]})
    bilete = doc.get("bilete", []) if doc else []
    bilet = next((b for b in bilete if b["cod"] == code), None)
    if not bilet:
        raise HTTPException(status_code=404, detail="Ticket not found for client")
    # Chain validare la Event Service
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{EVENT_SERVICE_URL}/validate/ticket", json={"code": code}, headers={"Authorization": f"Bearer dummy"})
            r.raise_for_status()
        except Exception:
            raise HTTPException(status_code=502, detail="Event service unavailable")
    valid = r.json().get("valid", False)
    if not valid:
        raise HTTPException(status_code=400, detail="Ticket invalid")
    # Adaugă detalii despre eveniment/pachet dacă există
    details = {"cod": code, "valid": True, "tip": bilet.get("tip")}
    async with httpx.AsyncClient() as client:
        if bilet.get("tip") == "eveniment" and bilet.get("eveniment"):
            # Exemplu: aduce detalii eveniment (presupunem că avem event_id salvat sau îl obținem din bilet)
            # Pentru demo, folosim nume și locație din bilet
            details["eveniment"] = bilet["eveniment"]
        elif bilet.get("tip") == "pachet" and bilet.get("pachet"):
            details["pachet"] = bilet["pachet"]
    return details
