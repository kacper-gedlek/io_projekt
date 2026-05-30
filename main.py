import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import database as db
from sqlalchemy import text


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
        session.execute(text("SELECT 1"))
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
    
@app.get("/user/{user_id}/courses")
def get_user_courses(user_id: int, session: Session = Depends(get_db)): # ZMIANA: db -> session
    # Sprawdzamy, czy użytkownik istnieje (usunąłem db.User.deleted == 0, bo nie ma tego w modelu w database.py)
    user = session.query(db.User).filter(db.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")
        
    # Wykonujemy zapytanie z JOINami analogicznie do SQL
    # SQLAlchemy pozwala pisać surowy SQL za pomocą text()
    from sqlalchemy import text
    
    query = text("""
        SELECT c.id, c.fullname 
        FROM moodle.mdl_user_enrolments ue
        JOIN moodle.mdl_enrol e ON e.id = ue.enrolid
        JOIN moodle.mdl_course c ON c.id = e.courseid
        WHERE ue.userid = :user_id
    """)
    
    result = session.execute(query, {"user_id": user_id}).fetchall()
    
    # Jeśli użytkownik istnieje, ale nie ma kursów
    if not result:
        return {
            "user": f"{user.firstname} {user.lastname}",
            "status": "Użytkownik nie jest zapisany na żaden kurs"
        }
        
    # Zwracamy listę kursów
    courses_list = [{"course_id": row[0], "course_name": row[1]} for row in result]
    
    return {
        "user_id": user.id,
        "username": user.username,
        "name": f"{user.firstname} {user.lastname}",
        "enrolled_courses": courses_list
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)