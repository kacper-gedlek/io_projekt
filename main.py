import uvicorn
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
        
@app.get("/test-db")
def test_db(session: Session = Depends(get_db)):
    try:
        # To zapytanie sprawdza tylko czy baza odpowiada
        session.execute(db.text("SELECT 1"))
        return {"status": "Połączono pomyślnie!"}
    except Exception as e:
        return {"status": "Błąd", "details": str(e)}

@app.get("/user/{user_id}")
def read_user(user_id: int, session: Session = Depends(get_db)):
    user = session.query(db.User).filter(db.User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
    
    return {
        "id": user.id,
        "login": user.username,
        "full_name": f"{user.firstname} {user.lastname}",
        "email": user.email,
        "status": {
            "is_confirmed": bool(user.confirmed),
            "is_suspended": bool(user.suspended)
        },
        "last_seen": user.lastaccess,
        "department": user.department
    }
    


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)