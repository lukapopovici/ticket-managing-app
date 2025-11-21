from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from auth_service.db import Base, engine, SessionLocal
from auth_service import models, schemas, utils
from common.security import create_access_token
from typing import List

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Auth Service")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/auth/login", response_model=schemas.TokenOut)
def login(body: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not utils.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=user.email, role=user.role)
    return {"access_token": token}

@app.post("/users", response_model=schemas.UserOut)
def create_user(body: schemas.UserCreate, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(models.User.email == body.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already used")
    u = models.User(email=body.email, password_hash=utils.hash_password(body.password), role=body.role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@app.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()
