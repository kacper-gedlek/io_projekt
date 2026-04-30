from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import database as db

app = FastAPI()

# Połączenie z bazą
def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@app.get("/user/{user_id}")
def read_user(user_id: int, session: Session = Depends(get_db)):
    # Szukamy użytkownika po kolumnie 'id'
    user = session.query(db.User).filter(db.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Nie znaleziono użytkownika o podanym ID")
    
    # Zwracamy wszystkie dane z bazy w formacie JSON
    return {
        "id": user.id,
        "username": user.username,
        "firstname": user.firstname,
        "idnumber": user.idnumber,
        "auth": user.auth,
        "confirmed": user.confirmed,
        "policyagreed": user.policyagreed,
        "deleted": user.deleted,
        "suspended": user.suspended,
        "mnethostid": user.mnethostid
        # Hasła celowo nie zwracamy ze względów bezpieczeństwa
    }