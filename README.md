# POS Project Python

## Overview
This project simulates a platform for managing events, event packages, tickets, and clients. It consists of two main services:
- **Event Service**: Manages events, packages, and tickets (SQLite)
- **Client Service**: Manages client profiles and their tickets (MongoDB)

---

## Dependencies

### Python Packages
- fastapi
- uvicorn
- sqlalchemy
- httpx
- motor
- pymongo

Install with:
```bash
pip install fastapi uvicorn sqlalchemy httpx motor pymongo
```

### Databases
- **SQLite**: Used by Event Service
  - File: `event.db`
- **MongoDB**: Used by Client Service
  - Database: `pos_client`
  - Collection: `clients`

---

## Database Structures

### SQLite (Event Service)
- **events**
  - id (int, PK)
  - id_owner (int)
  - name (str, unique)
  - location (str)
  - description (str)
  - seats (int)
- **packages**
  - id (int, PK)
  - id_owner (int)
  - name (str, unique)
  - location (str)
  - description (str)
  - seats (int)
- **package_events**
  - package_id (int, FK)
  - event_id (int, FK)
- **tickets**
  - code (str, PK)
  - package_id (int, FK, nullable)
  - event_id (int, FK, nullable)

### MongoDB (Client Service)
- **Database**: `pos_client`
- **Collection**: `clients`
- **Document Structure**:
  ```json
  {
    "_id": ObjectId,
    "email": "string",
    "prenume": "string",
    "nume": "string",
    "public": true/false,
    "social": ["url1", "url2", ...],
    "bilete": [
      {
        "cod": "string",
        "tip": "eveniment" | "pachet",
        "eveniment": {"nume": "string", "locatie": "string"},
        "pachet": {"nume": "string"}
      }
    ]
  }
  ```

---

## API Routes

### Event Service (FastAPI, SQLite)
- `GET /events` — List events (filter, paginate)
- `POST /events` — Create event
- `PUT /events/{event_id}` — Update event
- `GET /events/{event_id}/event-packets` — Get packages for event
- `GET /event-packets/{package_id}/events` — Get events in package
- `POST /packages` — Create package
- `GET /event-packets` — List packages (filter, paginate)
- `POST /tickets` — Create ticket
- `POST /validate/ticket` — Validate ticket
- `GET /events/{event_id}/tickets/{ticket_id}` — Get ticket for event
- `GET /event-packets/{package_id}/tickets/{ticket_id}` — Get ticket for package

### Client Service (FastAPI, MongoDB)
- `GET /clients` — Info + HATEOAS links
- `POST /clients/me` — Create profile
- `GET /clients/me` — Get profile
- `PUT /clients/me` — Update profile
- `GET /clients/me/tickets` — List client tickets
- `POST /clients/me/tickets` — Add ticket (validate via Event Service)
- `GET /clients/me/tickets/{code}/details` — Get ticket details (validate + event/package info)

---

## Running the Services

1. **Start MongoDB** (default: `mongodb://localhost:27017`)
2. **Run Event Service**
   ```bash
   uvicorn event_service.main:app --reload --port 8001
   ```
3. **Run Client Service**
   ```bash
   uvicorn client_service.main:app --reload --port 8002
   ```

---

## Notes
- Test endpoints with Postman or curl.
- Environment variables:
  - `EVENT_SERVICE_URL` (default: `http://localhost:8001`)
  - `MONGO_URL` (default: `mongodb://localhost:27017`)
  - `MONGO_DB` (default: `pos_client`)

---
