# main.py
import os
from fastapi import FastAPI, Depends, HTTPException
from db import engine, SessionLocal, Base
import models
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

# create tables (if you prefer SQL file, you can skip this)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Health Chatbot Backend (Prototype)")

# Pydantic model for /query POST body
class QueryIn(BaseModel):
    phone: str
    message: str
    channel: str = "whatsapp"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

@app.post("/query")
def receive_query(payload: QueryIn, db: Session = Depends(get_db)):
    # find or create user
    user = db.query(models.User).filter(models.User.phone == payload.phone).first()
    if not user:
        user = models.User(phone=payload.phone)
        db.add(user)
        db.commit()
        db.refresh(user)

    q = models.Query(user_id=user.id, channel=payload.channel, message_text=payload.message, status="received")
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"query_id": q.id, "status": "saved"}
