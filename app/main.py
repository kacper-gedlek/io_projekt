from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import time
from datetime import datetime, date as DateType

from app.database import get_db
from app.config import settings
from app import crud

app = FastAPI(
    title="Moodle Mifare Integration API",
    description="API do integracji czytników kart Mifare z wtyczką Attendance w Moodle",
    version="1.0.0"
)

# CORS Middleware (zezwolenie na komunikację z aplikacjami frontendowymi)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Zabezpieczenie API kluczem X-API-Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if not settings.API_KEY:
        return None  # Brak wymogu klucza jeśli nie jest skonfigurowany
    if api_key == settings.API_KEY:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Niepoprawny lub brakujący klucz API (X-API-Key)."
    )

# Modele Pydantic do walidacji danych wejściowych/wyjściowych
class UserResponse(BaseModel):
    id: int
    username: str
    firstname: str
    lastname: str
    email: str
    idnumber: str

    class Config:
        from_attributes = True

class CourseResponse(BaseModel):
    id: int
    fullname: str
    shortname: str

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    sessdate: int          # surowy Unix timestamp (kompatybilność wsteczna)
    duration: int          # surowy czas trwania w sekundach (kompatybilność wsteczna)
    description: str
    attendance_name: str
    # Czytelne pola dla frontendu
    date: str              # np. "2025-05-30"
    time_start: str        # np. "18:00"
    time_end: str          # np. "19:30"
    duration_label: str    # np. "1h 30min"
    label: str             # np. "Piątek, 30.05.2025 · 18:00–19:30"

    class Config:
        from_attributes = True


def _build_session_response(row) -> SessionResponse:
    """Przetwarza wiersz z bazy na SessionResponse z czytelnymi polami daty/czasu."""
    dt_start = datetime.fromtimestamp(row.sessdate)
    dt_end = datetime.fromtimestamp(row.sessdate + row.duration)

    total_minutes = row.duration // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0 and minutes > 0:
        duration_label = f"{hours}h {minutes}min"
    elif hours > 0:
        duration_label = f"{hours}h"
    else:
        duration_label = f"{minutes}min"

    day_names = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
    day_name = day_names[dt_start.weekday()]

    return SessionResponse(
        id=row.id,
        sessdate=row.sessdate,
        duration=row.duration,
        description=row.description,
        attendance_name=row.attendance_name,
        date=dt_start.strftime("%Y-%m-%d"),
        time_start=dt_start.strftime("%H:%M"),
        time_end=dt_end.strftime("%H:%M"),
        duration_label=duration_label,
        label=f"{day_name}, {dt_start.strftime('%d.%m.%Y')} · {dt_start.strftime('%H:%M')}–{dt_end.strftime('%H:%M')}",
    )

class AttendanceRegisterRequest(BaseModel):
    session_id: int
    student_card_uid: str

class AttendanceRegisterResponse(BaseModel):
    status: str
    message: str
    student: str
    session_id: int
    registered_at: int


@app.get("/")
def read_root():
    return {
        "message": "Moodle Mifare API działa poprawnie.",
        "documentation": "/docs"
    }


@app.get(
    "/api/users/check/{card_uid}",
    response_model=UserResponse,
    dependencies=[Depends(verify_api_key)]
)
def check_user(card_uid: str, db: Session = Depends(get_db)):
    """Sprawdza, czy karta o podanym UID Mifare jest przypisana do aktywnego użytkownika Moodle."""
    user = crud.get_user_by_card_uid(db, card_uid)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Użytkownik z kartą Mifare UID '{card_uid}' nie został znaleziony w bazie Moodle."
        )
    return user


@app.get(
    "/api/lecturer/{card_uid}/courses",
    response_model=List[CourseResponse],
    dependencies=[Depends(verify_api_key)]
)
def get_lecturer_courses(card_uid: str, db: Session = Depends(get_db)):
    """Pobiera listę przedmiotów (kursów) prowadzonych przez wykładowcę po zeskanowaniu jego karty."""
    # 1. Znajdź użytkownika
    lecturer = crud.get_user_by_card_uid(db, card_uid)
    if not lecturer:
        raise HTTPException(
            status_code=404,
            detail="Prowadzący z tą kartą Mifare nie został znaleziony."
        )

    # 2. Pobierz kursy
    courses = crud.get_lecturer_courses(db, lecturer.id)
    if not courses:
        raise HTTPException(
            status_code=404,
            detail="Ten wykładowca nie ma przypisanych aktywnych kursów jako prowadzący."
        )
    return courses


@app.get(
    "/api/courses/{course_id}/sessions",
    response_model=List[SessionResponse],
    dependencies=[Depends(verify_api_key)]
)
def get_course_sessions(
    course_id: int,
    db: Session = Depends(get_db),
    date: Optional[str] = None  # format: "YYYY-MM-DD" lub "all" żeby pobrać wszystkie
):
    """
    Pobiera sesje obecności dla wybranego kursu.

    - **Domyślnie** (bez parametru `date`): zwraca tylko dzisiejsze sesje.
    - `?date=2025-05-30` — sesje z konkretnego dnia.
    - `?date=all` — wszystkie sesje (historia całego semestru).
    """
    filter_date: Optional[DateType] = None  # None = domyślny filtr (dziś) w crud

    if date is not None:
        if date.lower() == "all":
            # Wyłącz filtrowanie — ustaw specjalny sentinel w crud
            sessions = crud.get_course_sessions(db, course_id, filter_date="all")
            return [_build_session_response(s) for s in sessions]
        try:
            filter_date = DateType.fromisoformat(date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Niepoprawny format daty. Użyj YYYY-MM-DD lub 'all'."
            )

    sessions = crud.get_course_sessions(db, course_id, filter_date=filter_date)
    return [_build_session_response(s) for s in sessions]


@app.post(
    "/api/attendance/register",
    response_model=AttendanceRegisterResponse,
    dependencies=[Depends(verify_api_key)]
)
def register_attendance(
    request: AttendanceRegisterRequest,
    db: Session = Depends(get_db)
):
    """Rejestruje obecność studenta po zeskanowaniu jego karty Mifare na wybranej sesji zajęć."""
    # 1. Znajdź studenta po UID karty Mifare
    student = crud.get_user_by_card_uid(db, request.student_card_uid)
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student o karcie Mifare UID '{request.student_card_uid}' nie istnieje w bazie Moodle."
        )

    # 2. Zapisz obecność
    try:
        log = crud.register_student_attendance(
            db=db,
            session_id=request.session_id,
            student_id=student.id
        )
        
        student_name = f"{student.firstname} {student.lastname}".strip()
        if not student_name:
            student_name = student.username

        return AttendanceRegisterResponse(
            status="success",
            message=f"Pomyślnie zarejestrowano obecność dla studenta: {student_name}",
            student=student_name,
            session_id=request.session_id,
            registered_at=log.timetaken
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas rejestracji obecności: {str(e)}"
        )
