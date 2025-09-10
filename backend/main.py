import os
import csv
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db import engine, SessionLocal, Base
from backend import models

# Auto-create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Health Chatbot Backend (Prototype)")

# ---------------------------
# Pydantic Schemas
# ---------------------------
class QueryIn(BaseModel):
    phone: str
    message: str
    channel: str = "whatsapp"

class QueryOut(BaseModel):
    query_id: int
    status: str

# ---------------------------
# DB Dependency
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# Routes
# ---------------------------
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@app.post("/query", response_model=QueryOut)
def receive_query(payload: QueryIn, db: Session = Depends(get_db)):
    # find or create user
    user = db.query(models.User).filter(models.User.phone == payload.phone).first()
    if not user:
        user = models.User(phone=payload.phone)
        db.add(user)
        db.commit()
        db.refresh(user)

    # save query
    q = models.Query(
        user_id=user.id,
        channel=payload.channel,
        message_text=payload.message,
        status="received"
    )
    db.add(q)
    db.commit()
    db.refresh(q)

    return {"query_id": q.id, "status": "saved"}


@app.post("/ask-ml")
def ask_ml(question: str):
    # 🚧 Placeholder - connect to MedGemma/RAG later
    return {"answer": f"Stub response for: {question}"}


@app.get("/faq")
def get_faq():
    faqs = []
    FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "knowledge_base_docs", "test_queries.csv")

    if not os.path.exists(FAQ_PATH):
        return {"faqs": [], "error": "FAQ file not found"}

    with open(FAQ_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            faqs.append({
                "id": row["query_id"],
                "category": row["category"],
                "question": row["question"],
                "answer": row["answer"]
            })
    return {"faqs": faqs}


@app.post("/webhook/twilio", response_class=PlainTextResponse)
def twilio_webhook(
    From: str = Form(...),  # sender's phone number
    Body: str = Form(...),  # message text
    To: str = Form(...),    # your Twilio number
    db: Session = Depends(get_db)
):
    phone = From.replace("whatsapp:", "").strip()

    # Find or create user
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if not user:
        user = models.User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Save query
    q = models.Query(
        user_id=user.id,
        channel="whatsapp",
        message_text=Body,
        status="received"
    )
    db.add(q)
    db.commit()
    db.refresh(q)

    # --- Call ML Stub (replace later with MedGemma API call) ---
    answer = f"Stub response: I received your message '{Body}'. Stay tuned for AI-powered answer!"

    # Save AI response
    q.response_text = answer
    q.status = "answered"
    db.commit()

    # Respond to Twilio (plain text)
    return answer
