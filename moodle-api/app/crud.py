import time
from sqlalchemy.orm import Session
from app.models import (
    MoodleUser,
    MoodleCourse,
    MoodleContext,
    MoodleRoleAssignment,
    MoodleRole,
    MoodleAttendance,
    MoodleAttendanceSession,
    MoodleAttendanceStatus,
    MoodleAttendanceLog
)

def get_user_by_card_uid(db: Session, card_uid: str) -> MoodleUser:
    """Wyszukuje aktywnego użytkownika w Moodle na podstawie UID karty (pole idnumber)."""
    return db.query(MoodleUser).filter(
        MoodleUser.idnumber == card_uid,
        MoodleUser.deleted == False,
        MoodleUser.suspended == False
    ).first()

def get_lecturer_courses(db: Session, lecturer_id: int):
    """Pobiera listę kursów, w których wykładowca ma rolę 'teacher' lub 'editingteacher'."""
    return (
        db.query(MoodleCourse)
        .join(MoodleContext, (MoodleContext.instanceid == MoodleCourse.id) & (MoodleContext.contextlevel == 50))
        .join(MoodleRoleAssignment, MoodleRoleAssignment.contextid == MoodleContext.id)
        .join(MoodleRole, MoodleRole.id == MoodleRoleAssignment.roleid)
        .filter(MoodleRoleAssignment.userid == lecturer_id)
        .filter(MoodleRole.shortname.in_(["teacher", "editingteacher"]))
        .all()
    )

def get_course_sessions(db: Session, course_id: int):
    """Pobiera wszystkie sesje obecności (z wtyczki attendance) powiązane z danym kursem."""
    return (
        db.query(
            MoodleAttendanceSession.id,
            MoodleAttendanceSession.sessdate,
            MoodleAttendanceSession.duration,
            MoodleAttendanceSession.description,
            MoodleAttendance.name.label("attendance_name")
        )
        .join(MoodleAttendance, MoodleAttendance.id == MoodleAttendanceSession.attendanceid)
        .filter(MoodleAttendance.course == course_id)
        .order_by(MoodleAttendanceSession.sessdate.desc())
        .all()
    )

def register_student_attendance(db: Session, session_id: int, student_id: int, taken_by_id: int = None):
    """
    Rejestruje obecność studenta na danej sesji.
    Znajduje status 'Present' (Obecny), tworzy zestaw statusów i zapisuje log w Moodle.
    """
    # 1. Pobierz sesję obecności
    session = db.query(MoodleAttendanceSession).filter(MoodleAttendanceSession.id == session_id).first()
    if not session:
        raise ValueError("Sesja obecności nie istnieje.")

    # 2. Pobierz wszystkie dostępne statusy dla tej aktywności obecności
    statuses = db.query(MoodleAttendanceStatus).filter(
        MoodleAttendanceStatus.attendanceid == session.attendanceid,
        MoodleAttendanceStatus.deleted == 0
    ).all()

    if not statuses:
        raise ValueError("Brak zdefiniowanych statusów obecności dla tej aktywności.")

    # 3. Znajdź status "Present" (zazwyczaj skrót 'P' lub najwyższa ocena)
    present_status = None
    for status in statuses:
        if status.acronym.upper() == 'P':
            present_status = status
            break
    
    # Fallback: jeśli nie ma 'P', weź status z najwyższą oceną (grade)
    if not present_status:
        present_status = max(statuses, key=lambda s: s.grade)

    # 4. Przygotuj statusset (lista id wszystkich aktywnych statusów rozdzielona przecinkami)
    statusset = ",".join(str(s.id) for s in statuses)

    # 5. Sprawdź, czy obecność jest już zarejestrowana
    existing_log = db.query(MoodleAttendanceLog).filter(
        MoodleAttendanceLog.sessionid == session_id,
        MoodleAttendanceLog.studentid == student_id
    ).first()

    current_time = int(time.time())
    # Kto dokonał rejestracji (jeśli nie podano, przypisujemy studentowi lub prowadzącemu)
    operator_id = taken_by_id if taken_by_id else student_id

    if existing_log:
        # Aktualizuj istniejący wpis na obecny (w przypadku np. zmiany z nieobecnego)
        existing_log.statusid = present_status.id
        existing_log.statusset = statusset
        existing_log.timetaken = current_time
        existing_log.takenby = operator_id
        db.commit()
        db.refresh(existing_log)
        return existing_log
    else:
        # Stwórz nowy wpis obecności
        new_log = MoodleAttendanceLog(
            sessionid=session_id,
            studentid=student_id,
            statusid=present_status.id,
            statusset=statusset,
            timetaken=current_time,
            takenby=operator_id
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
