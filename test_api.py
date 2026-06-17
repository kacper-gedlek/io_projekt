import os
import time

# Ustawiamy testowe zmienne środowiskowe przed importem modułów aplikacji
os.environ["DATABASE_URL"] = "sqlite:///./test_moodle.db"
os.environ["API_KEY"] = "mifare_super_secret_token_123"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importujemy komponenty naszej aplikacji
from app.database import Base, get_db
from app.main import app
from app.models import (
    MoodleUser,
    MoodleCourse,
    MoodleContext,
    MoodleRole,
    MoodleRoleAssignment,
    MoodleAttendance,
    MoodleAttendanceSession,
    MoodleAttendanceStatus,
    MoodleAttendanceLog
)

# 1. Konfiguracja testowej bazy danych w pamięci (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_moodle.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Nadpisanie zależności get_db w FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Stałe testowe dla kart Mifare
LECTURER_CARD = "LECTURER_123_UID"
STUDENT_CARD_1 = "STUDENT_456_UID"
STUDENT_CARD_2 = "STUDENT_789_UID"
API_KEY = "mifare_super_secret_token_123"

headers = {
    "X-API-Key": API_KEY
}

def setup_database():
    # Usuwamy starą bazę jeśli istnieje i tworzymy nową strukturę
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        # A. Dodanie użytkowników (Wykładowca i 2 Studentów)
        lecturer = MoodleUser(
            id=10,
            username="j.kowalski",
            firstname="Jan",
            lastname="Kowalski",
            email="jan.kowalski@uczelnia.pl",
            idnumber=LECTURER_CARD,
            deleted=False,
            suspended=False
        )
        student1 = MoodleUser(
            id=20,
            username="a.nowak",
            firstname="Anna",
            lastname="Nowak",
            email="anna.nowak@student.pl",
            idnumber=STUDENT_CARD_1,
            deleted=False,
            suspended=False
        )
        student2 = MoodleUser(
            id=21,
            username="m.wisniewski",
            firstname="Michal",
            lastname="Wisniewski",
            email="michal@student.pl",
            idnumber=STUDENT_CARD_2,
            deleted=False,
            suspended=False
        )
        db.add_all([lecturer, student1, student2])
        
        # B. Dodanie kursów
        course1 = MoodleCourse(id=101, fullname="Matematyka Dyskretna", shortname="MAT-DYS")
        course2 = MoodleCourse(id=102, fullname="Fizyka Kwantowa", shortname="FIZ-KWA")
        db.add_all([course1, course2])
        db.commit()

        # C. Nadanie wykładowcy roli prowadzącego ('editingteacher') w Kursie 1
        # W Moodle: Kurs id=101 ma context o id=5001 z contextlevel=50 (Course context)
        context1 = MoodleContext(id=5001, contextlevel=50, instanceid=101)
        role_teacher = MoodleRole(id=3, shortname="editingteacher")
        role_assignment = MoodleRoleAssignment(
            id=99,
            roleid=3,
            contextid=5001,
            userid=10  # Jan Kowalski
        )
        db.add_all([context1, role_teacher, role_assignment])
        db.commit()

        # D. Dodanie modułu obecności (Attendance) do Kursu 1
        attendance = MoodleAttendance(id=301, course=101, name="Obecność - Wykład")
        db.add(attendance)
        db.commit()

        # E. Definiowanie statusów obecności dla tej aktywności (np. P=Present, A=Absent)
        status_present = MoodleAttendanceStatus(
            id=401,
            attendanceid=301,
            acronym="P",
            description="Present",
            grade=2.0,
            deleted=0
        )
        status_absent = MoodleAttendanceStatus(
            id=402,
            attendanceid=301,
            acronym="A",
            description="Absent",
            grade=0.0,
            deleted=0
        )
        db.add_all([status_present, status_absent])
        db.commit()

        # F. Dodanie sesji obecności (zajęć) w tej instancji
        session = MoodleAttendanceSession(
            id=501,
            attendanceid=301,
            sessdate=int(time.time()),
            duration=5400,  # 1.5 godziny
            description="Wyklad Wprowadzajacy"
        )
        db.add(session)
        db.commit()

    finally:
        db.close()


def test_api_endpoints():
    print("--- URUCHAMIANIE TESTOW API ---")
    setup_database()

    # Test 0: Brak klucza API
    print("Test 0: Weryfikacja braku klucza API...")
    res = client.get(f"/api/users/check/{LECTURER_CARD}")
    assert res.status_code == 403, "Oczekiwano bledu 403 przy braku klucza API"
    print("[OK] Zabezpieczenie API dziala.")

    # Test 1: Sprawdzenie użytkownika (Wykładowca)
    print("Test 1: Sprawdzenie uzytkownika po karcie Mifare...")
    res = client.get(f"/api/users/check/{LECTURER_CARD}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "j.kowalski"
    assert data["firstname"] == "Jan"
    print("[OK] Pomyslnie zweryfikowano uzytkownika po karcie Mifare.")

    # Test 2: Sprawdzenie nieistniejącego użytkownika
    print("Test 2: Sprawdzenie nieistniejacego uzytkownika...")
    res = client.get("/api/users/check/UNKNOWN_CARD", headers=headers)
    assert res.status_code == 404
    print("[OK] API poprawnie zwraca 404 dla nieznanej karty.")

    # Test 3: Pobranie przedmiotów wykładowcy
    print("Test 3: Pobranie kursow dla wykladowcy...")
    res = client.get(f"/api/lecturer/{LECTURER_CARD}/courses", headers=headers)
    assert res.status_code == 200
    courses = res.json()
    assert len(courses) == 1
    assert courses[0]["shortname"] == "MAT-DYS"
    print(f"[OK] Znaleziono przedmioty wykladowcy: {courses[0]['fullname']}")

    # Test 4: Pobranie sesji obecności dla przedmiotu
    print("Test 4: Pobranie sesji obecnosci...")
    res = client.get("/api/courses/101/sessions", headers=headers)
    assert res.status_code == 200
    sessions = res.json()
    assert len(sessions) == 1
    assert sessions[0]["description"] == "Wyklad Wprowadzajacy"
    print(f"[OK] Znaleziono sesje obecnosci: {sessions[0]['description']}")

    # Test 5: Rejestracja obecności studenta
    print("Test 5: Rejestracja obecnosci studenta...")
    register_payload = {
        "session_id": 501,
        "student_card_uid": STUDENT_CARD_1
    }
    res = client.post("/api/attendance/register", json=register_payload, headers=headers)
    if res.status_code != 200:
        print(f"BLEDNY STATUS REJESTRACJI: {res.status_code}, TESC: {res.text}")
    assert res.status_code == 200
    reg_data = res.json()
    assert reg_data["status"] == "success"
    assert reg_data["student"] == "Anna Nowak"
    print(f"[OK] Zarejestrowano obecnosc: {reg_data['message']}")

    # Zweryfikujmy bazę danych pod kątem wstawionego rekordu logu
    db = TestingSessionLocal()
    try:
        log = db.query(MoodleAttendanceLog).filter(
            MoodleAttendanceLog.sessionid == 501,
            MoodleAttendanceLog.studentid == 20  # Anna Nowak
        ).first()
        assert log is not None, "Log obecnosci nie zostal zapisany w bazie!"
        assert log.statusid == 401, "Niepoprawne ID statusu obecnosci (oczekiwano 401)"
        print("[OK] Potwierdzono zapis w bazie danych Moodle (SQLite).")
    finally:
        db.close()

    print("\n[SUCCESS] WSZYSTKIE TESTY ZAKONCZONE POMYSLNIE! [SUCCESS]")

if __name__ == "__main__":
    test_api_endpoints()
    
    # Zamkniecie polaczen przed usunieciem pliku
    engine.dispose()
    
    # Czyszczenie bazy testowej
    if os.path.exists("./test_moodle.db"):
        try:
            os.remove("./test_moodle.db")
        except Exception:
            pass
