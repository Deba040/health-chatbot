# send_reminders.py
from backend.db import SessionLocal
from backend import models
from datetime import date

def run():
    db = SessionLocal()
    today = date.today().isoformat()

    reminders = db.query(models.Reminder).filter(
        models.Reminder.due_date == today,
        models.Reminder.status == "pending"
    ).all()

    for r in reminders:
        print(f"[Reminder] User {r.user_id} needs {r.vaccine_name} today")
        r.status = "sent"
        db.commit()

    db.close()

if __name__ == "__main__":
    run()
