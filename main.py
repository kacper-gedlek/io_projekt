import os
import time
from datetime import datetime
import requests
import uvicorn

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

MOODLE_API_URL = os.getenv("MOODLE_API_URL", "https://moodle.maruda-lab.org/moodle-api")
MOODLE_API_KEY = os.getenv("MOODLE_API_KEY")
ROOM_NAME = os.getenv("ROOM_NAME", "Aula 2.14")

if not MOODLE_API_KEY:
    raise RuntimeError("Brakuje MOODLE_API_KEY w pliku .env")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


last_scan = {
    "uid": None,
    "user": None,
    "status": "waiting",
    "message": "Przyłóż kartę RFID, aby zalogować obecność.",
    "scanned_at": None,
    "attendance": None,
    "session_id": None,
    "course_id": None,
}

teacher_auth = {
    "active": False,
    "status": "idle",
    "uid": None,
    "user": None,
    "courses": [],
    "sessions": [],
    "started_at": None,
}

selected_context = {
    "lecturer_uid": None,
    "lecturer_name": None,
    "course_id": None,
    "course": None,
    "session_id": None,
    "session": None,
}

SCAN_COOLDOWN_SECONDS = 2


def api_headers():
    return {
        "X-API-Key": MOODLE_API_KEY,
        "accept": "application/json",
    }


def normalize_uid(uid: str) -> str:
    return str(uid).replace("-", "").replace(" ", "").strip()


def moodle_get(path: str):
    url = f"{MOODLE_API_URL}{path}"

    try:
        response = requests.get(url, headers=api_headers(), timeout=10)
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Nie udało się połączyć z Moodle API: {str(e)}"
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return response.json()


def moodle_post(path: str, payload: dict):
    url = f"{MOODLE_API_URL}{path}"

    try:
        response = requests.post(url, json=payload, headers=api_headers(), timeout=10)
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Nie udało się połączyć z Moodle API: {str(e)}"
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return response.json()


def check_user_by_card(card_uid: str):
    card_uid = normalize_uid(card_uid)
    return moodle_get(f"/api/users/check/{card_uid}")


def get_lecturer_courses(card_uid: str):
    card_uid = normalize_uid(card_uid)
    return moodle_get(f"/api/lecturer/{card_uid}/courses")


def get_course_sessions(course_id: int):
    return moodle_get(f"/api/courses/{course_id}/sessions")


def register_attendance(session_id: int, student_card_uid: str):
    payload = {
        "session_id": int(session_id),
        "student_card_uid": normalize_uid(student_card_uid),
    }

    return moodle_post("/api/attendance/register", payload)


def get_user_full_name(user):
    if not user:
        return ""

    return f"{user.get('firstname', '')} {user.get('lastname', '')}".strip()


def get_session_id(session):
    if not session:
        return None

    for key in ["session_id", "id"]:
        if key in session:
            return session[key]

    return None


def find_session_by_id(sessions, session_id: int):
    for session in sessions:
        current_id = get_session_id(session)

        if current_id is not None and int(current_id) == int(session_id):
            return session

    return None


def build_session_option(course, session):
    return {
        **session,
        "course_id": course.get("id"),
        "course_name": course.get("fullname", "Kurs Moodle"),
        "course_shortname": course.get("shortname", "-"),
    }

def get_session_date(session):
    if not session:
        return None

    if session.get("date"):
        try:
            return datetime.strptime(session["date"], "%Y-%m-%d").date()
        except Exception:
            pass

    if session.get("sessdate"):
        try:
            return datetime.fromtimestamp(int(session["sessdate"])).date()
        except Exception:
            pass

    return None

def build_sessions_for_lecturer(card_uid: str):
    courses = get_lecturer_courses(card_uid)
    all_sessions = []

    today = datetime.now().date()

    for course in courses:
        course_id = course.get("id")

        if not course_id:
            continue

        try:
            sessions = get_course_sessions(course_id)
        except HTTPException:
            sessions = []

        for session in sessions:
            session_date = get_session_date(session)

            if session_date and session_date < today:
                continue

            all_sessions.append(build_session_option(course, session))

    def session_sort_key(session):
        try:
            return int(session.get("sessdate", 0))
        except Exception:
            return 0

    all_sessions.sort(key=session_sort_key)

    return courses, all_sessions


def extract_hour(value):
    value = str(value)

    if "T" in value:
        try:
            return value.split("T")[1][:5]
        except Exception:
            return value

    if " " in value:
        try:
            return value.split(" ")[1][:5]
        except Exception:
            return value

    if len(value) >= 5:
        return value[:5]

    return value


def format_session_duration(session):
    if not session:
        return "-"

    if "time_start" in session and "time_end" in session:
        return f"{session['time_start']}–{session['time_end']}"

    if "start_time" in session and "end_time" in session:
        return f"{extract_hour(session['start_time'])}–{extract_hour(session['end_time'])}"

    if "startTime" in session and "endTime" in session:
        return f"{extract_hour(session['startTime'])}–{extract_hour(session['endTime'])}"

    if "sessdate" in session and "duration" in session:
        try:
            start_ts = int(session["sessdate"])
            end_ts = start_ts + int(session["duration"])
            start_hour = datetime.fromtimestamp(start_ts).strftime("%H:%M")
            end_hour = datetime.fromtimestamp(end_ts).strftime("%H:%M")
            return f"{start_hour}–{end_hour}"
        except Exception:
            return "-"

    return "-"


def get_session_status(session):
    if not session:
        return "Brak aktywnych zajęć"

    now = int(time.time())

    if "sessdate" in session and "duration" in session:
        try:
            start_ts = int(session["sessdate"])
            end_ts = start_ts + int(session["duration"])

            if start_ts <= now <= end_ts:
                return "Zajęcia trwają"

            if now < start_ts:
                return "Nadchodzące zajęcia"

            return "Zajęcia zakończone"
        except Exception:
            pass

    return "Dane z Moodle API"

def is_session_finished(session):
    if not session:
        return False

    now = int(time.time())

    if "sessdate" in session and "duration" in session:
        try:
            start_ts = int(session["sessdate"])
            end_ts = start_ts + int(session["duration"])
            return now > end_ts
        except Exception:
            return False

    return False

def clear_selected_context():
    global selected_context

    selected_context = {
        "lecturer_uid": None,
        "lecturer_name": None,
        "course_id": None,
        "course": None,
        "session_id": None,
        "session": None,
    }

def has_active_class():
    return bool(selected_context.get("course") and selected_context.get("session"))


def get_panel_message():
    now = int(time.time())
    scanned_at = last_scan.get("scanned_at")

    scan_is_active = False
    if scanned_at:
        scan_is_active = now - int(scanned_at) < SCAN_COOLDOWN_SECONDS

    if not scan_is_active:
        return "Przyłóż kartę RFID, aby zalogować obecność."

    if last_scan["uid"] and last_scan["user"]:
        student_name = get_user_full_name(last_scan["user"])

        if last_scan["status"] == "attendance_registered":
            return f"{student_name} — obecność została zapisana."

        if last_scan["status"] == "attendance_error":
            return f"{student_name} — karta odczytana, ale nie udało się zapisać obecności."

        return f"{student_name} — karta odczytana poprawnie."

    if last_scan["uid"]:
        if last_scan.get("status") == "no_active_class":
            return "Brak aktywnych zajęć. Poproś prowadzącego o rozpoczęcie zajęć."

        if last_scan.get("status") == "class_finished":
            return "Zajęcia zostały zakończone. Sala wolna."

        if last_scan.get("status") == "unknown_card":
            return "Nie znaleziono użytkownika przypisanego do tej karty."

        return last_scan.get("message") or "Karta odczytana."

    return "Przyłóż kartę RFID, aby zalogować obecność."


def get_free_room_panel():
    return {
        "room": ROOM_NAME,
        "subject": "Sala wolna",
        "teacher": "-",
        "direction": "-",
        "duration": "-",
        "status": "Brak aktywnych zajęć",
        "message": get_panel_message(),
        "course_id": None,
        "session": None,
    }


@app.get("/")
def root():
    return {
        "status": "Backend FastAPI działa",
        "source": "Moodle Mifare Integration API",
    }


@app.get("/debug-config")
def debug_config():
    return {
        "MOODLE_API_URL": MOODLE_API_URL,
        "has_api_key": bool(MOODLE_API_KEY),
        "api_key_length": len(MOODLE_API_KEY) if MOODLE_API_KEY else 0,
        "api_key_start": MOODLE_API_KEY[:6] if MOODLE_API_KEY else None,
        "room_name": ROOM_NAME,
        "selected_context": selected_context,
        "teacher_auth": teacher_auth,
    }


@app.get("/api/panel")
def get_panel_data():
    if has_active_class() and is_session_finished(selected_context.get("session")):
        clear_selected_context()
        return get_free_room_panel()

    if not has_active_class():
        return get_free_room_panel()

    course = selected_context["course"]
    session = selected_context["session"]

    course_id = course.get("id")
    course_name = course.get("fullname", "Kurs Moodle")
    lecturer_name = selected_context.get("lecturer_name") or "Prowadzący"

    attendance_name = "-"
    if session:
        attendance_name = (
            session.get("attendance_name")
            or session.get("name")
            or session.get("description")
            or "-"
        )

    return {
        "room": ROOM_NAME,
        "subject": course_name,
        "teacher": lecturer_name,
        "direction": attendance_name,
        "duration": format_session_duration(session),
        "status": get_session_status(session),
        "message": get_panel_message(),
        "course_id": course_id,
        "session": session,
    }


@app.post("/api/teacher/auth/start")
def start_teacher_auth():
    global teacher_auth

    teacher_auth = {
        "active": True,
        "status": "waiting",
        "uid": None,
        "user": None,
        "courses": [],
        "sessions": [],
        "started_at": int(time.time()),
    }

    return teacher_auth


@app.post("/api/teacher/auth/cancel")
def cancel_teacher_auth():
    global teacher_auth

    teacher_auth = {
        "active": False,
        "status": "idle",
        "uid": None,
        "user": None,
        "courses": [],
        "sessions": [],
        "started_at": None,
    }

    return teacher_auth


@app.get("/api/teacher/auth/status")
def get_teacher_auth_status():
    return teacher_auth


@app.post("/api/teacher/select-session")
def select_teacher_session(payload: dict = Body(...)):
    global selected_context, teacher_auth, last_scan

    course_id = int(payload.get("course_id"))
    session_id = int(payload.get("session_id"))

    lecturer_uid = teacher_auth.get("uid")

    if not lecturer_uid:
        raise HTTPException(
            status_code=400,
            detail="Brak zalogowanego prowadzącego."
        )

    courses = get_lecturer_courses(lecturer_uid)

    selected_course = None
    selected_session = None

    for course in courses:
        if int(course.get("id")) != course_id:
            continue

        selected_course = course
        sessions = get_course_sessions(course_id)
        selected_session = find_session_by_id(sessions, session_id)
        break

    if not selected_course or not selected_session:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono wybranych zajęć."
        )
    try:
        lecturer_user = check_user_by_card(lecturer_uid)
        lecturer_name = get_user_full_name(lecturer_user) or "Prowadzący"
    except HTTPException:
        lecturer_user = None
        lecturer_name = "Prowadzący"

    selected_context = {
        "lecturer_uid": lecturer_uid,
        "lecturer_name": lecturer_name,
        "course_id": course_id,
        "course": selected_course,
        "session_id": session_id,
        "session": selected_session,
    }

    teacher_auth = {
        "active": False,
        "status": "selected",
        "uid": lecturer_uid,
        "user": lecturer_user,
        "courses": courses,
        "sessions": [],
        "started_at": None,
    }

    last_scan = {
        "uid": None,
        "user": None,
        "status": "waiting",
        "message": "Przyłóż kartę RFID, aby zalogować obecność.",
        "scanned_at": None,
        "attendance": None,
        "session_id": None,
        "course_id": None,
    }

    return {
        "status": "selected",
        "selected_context": selected_context,
    }


@app.post("/api/rfid/{uid}")
def scan_rfid(uid: str):
    global last_scan, teacher_auth

    normalized_uid = normalize_uid(uid)
    now = int(time.time())

    if teacher_auth.get("active"):
        try:
            courses, sessions = build_sessions_for_lecturer(normalized_uid)

            if not courses:
                teacher_auth = {
                    "active": False,
                    "status": "rejected",
                    "uid": normalized_uid,
                    "user": None,
                    "courses": [],
                    "sessions": [],
                    "started_at": teacher_auth.get("started_at"),
                }

                return teacher_auth

            try:
                user = check_user_by_card(normalized_uid)
            except HTTPException:
                user = None

            teacher_auth = {
                "active": True,
                "status": "authorized",
                "uid": normalized_uid,
                "user": user,
                "courses": courses,
                "sessions": sessions,
                "started_at": teacher_auth.get("started_at"),
            }

            return teacher_auth

        except HTTPException:
            teacher_auth = {
                "active": False,
                "status": "rejected",
                "uid": normalized_uid,
                "user": None,
                "courses": [],
                "sessions": [],
                "started_at": teacher_auth.get("started_at"),
            }

            return teacher_auth

    if has_active_class() and is_session_finished(selected_context.get("session")):
        clear_selected_context()

        last_scan = {
            "uid": normalized_uid,
            "user": None,
            "status": "class_finished",
            "message": "Zajęcia zostały zakończone. Sala wolna.",
            "scanned_at": now,
            "attendance": None,
            "session_id": None,
            "course_id": None,
        }

        return last_scan

    if not has_active_class():
        last_scan = {
            "uid": normalized_uid,
            "user": None,
            "status": "no_active_class",
            "message": "Brak aktywnych zajęć. Poproś prowadzącego o rozpoczęcie zajęć.",
            "scanned_at": now,
            "attendance": None,
            "session_id": None,
            "course_id": None,
        }

        return last_scan

    if last_scan.get("scanned_at"):
        seconds_since_last_scan = now - int(last_scan["scanned_at"])

        if seconds_since_last_scan < SCAN_COOLDOWN_SECONDS:
            remaining = SCAN_COOLDOWN_SECONDS - seconds_since_last_scan

            return {
                "uid": normalized_uid,
                "status": "cooldown",
                "message": f"Poczekaj {remaining}s przed kolejnym odczytem.",
                "cooldown_remaining": remaining,
                "last_scan": last_scan,
            }

    try:
        user = check_user_by_card(normalized_uid)
    except HTTPException:
        last_scan = {
            "uid": normalized_uid,
            "user": None,
            "status": "unknown_card",
            "message": "Nie znaleziono użytkownika przypisanego do tej karty.",
            "scanned_at": now,
            "attendance": None,
            "session_id": None,
            "course_id": None,
        }

        return last_scan

    try:
        session_id = selected_context.get("session_id")
        course_id = selected_context.get("course_id")

        if not session_id:
            raise HTTPException(
                status_code=404,
                detail="Nie znaleziono session_id dla zajęć."
            )

        attendance_response = register_attendance(session_id, normalized_uid)
        student_name = get_user_full_name(user)

        last_scan = {
            "uid": normalized_uid,
            "user": user,
            "status": "attendance_registered",
            "message": f"{student_name} — obecność została zapisana.",
            "scanned_at": now,
            "attendance": attendance_response,
            "session_id": session_id,
            "course_id": course_id,
        }

        return last_scan

    except HTTPException as e:
        student_name = get_user_full_name(user)

        last_scan = {
            "uid": normalized_uid,
            "user": user,
            "status": "attendance_error",
            "message": f"{student_name} — karta odczytana, ale nie udało się zapisać obecności.",
            "scanned_at": now,
            "attendance": None,
            "session_id": selected_context.get("session_id"),
            "course_id": selected_context.get("course_id"),
            "error": e.detail,
        }

        return last_scan


@app.get("/api/rfid")
def get_last_rfid():
    return last_scan


@app.post("/api/end-class")
def end_class():
    global selected_context, last_scan

    selected_context = {
        "lecturer_uid": None,
        "lecturer_name": None,
        "course_id": None,
        "course": None,
        "session_id": None,
        "session": None,
    }

    last_scan = {
        "uid": None,
        "user": None,
        "status": "waiting",
        "message": "Przyłóż kartę RFID, aby zalogować obecność.",
        "scanned_at": None,
        "attendance": None,
        "session_id": None,
        "course_id": None,
    }

    return {
        "status": "ended",
        "message": "Zajęcia zakończone. Sala wolna."
    }


@app.get("/api/debug/user/{card_uid}")
def debug_user(card_uid: str):
    return check_user_by_card(card_uid)


@app.get("/api/debug/courses/{card_uid}")
def debug_courses_for_card(card_uid: str):
    return get_lecturer_courses(card_uid)


@app.get("/api/debug/courses/{course_id}/sessions")
def debug_sessions(course_id: int):
    return get_course_sessions(course_id)


@app.post("/api/debug/attendance/{session_id}/{student_card_uid}")
def debug_register_attendance(session_id: int, student_card_uid: str):
    return register_attendance(session_id, student_card_uid)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)