from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, BigInteger
from app.database import Base

# Typ ID kompatybilny z BIGINT na MySQL
MoodleID = Integer().with_variant(BigInteger, "mysql")

class MoodleUser(Base):
    __tablename__ = "mdl_user"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    firstname = Column(String(100), default="")
    lastname = Column(String(100), default="")
    email = Column(String(100), default="")
    idnumber = Column(String(255), index=True, default="")
    deleted = Column(Boolean, default=False)
    suspended = Column(Boolean, default=False)


class MoodleCourse(Base):
    __tablename__ = "mdl_course"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    fullname = Column(String(254), nullable=False)
    shortname = Column(String(100), nullable=False)


class MoodleContext(Base):
    __tablename__ = "mdl_context"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    contextlevel = Column(Integer, nullable=False)  # 50 = Kurs (CONTESTAT_COURSE)
    instanceid = Column(BigInteger, nullable=False)  # ID instancji (np. ID kursu)


class MoodleRole(Base):
    __tablename__ = "mdl_role"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    shortname = Column(String(100), nullable=False)  # np. 'teacher', 'editingteacher'


class MoodleRoleAssignment(Base):
    __tablename__ = "mdl_role_assignments"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    roleid = Column(BigInteger, nullable=False)
    contextid = Column(BigInteger, nullable=False)
    userid = Column(BigInteger, nullable=False)


# Wtyczka Attendance (mod_attendance)
class MoodleAttendance(Base):
    __tablename__ = "mdl_attendance"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    course = Column(BigInteger, nullable=False)  # ID kursu
    name = Column(String(255), nullable=False)


class MoodleAttendanceSession(Base):
    __tablename__ = "mdl_attendance_sessions"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    attendanceid = Column(BigInteger, nullable=False)  # Link do mdl_attendance
    sessdate = Column(BigInteger, nullable=False)  # Unix timestamp rozpoczęcia
    duration = Column(BigInteger, nullable=False)  # Czas trwania w sekundach
    description = Column(String(255), default="")


class MoodleAttendanceStatus(Base):
    __tablename__ = "mdl_attendance_statuses"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    attendanceid = Column(BigInteger, nullable=False)  # Link do mdl_attendance
    acronym = Column(String(2), nullable=False)  # np. 'P' (Present), 'A' (Absent)
    description = Column(String(30), nullable=False)
    grade = Column(Float, default=0.0)
    deleted = Column(Integer, default=0)  # 0 = aktywne, 1 = usunięte


class MoodleAttendanceLog(Base):
    __tablename__ = "mdl_attendance_log"

    id = Column(MoodleID, primary_key=True, index=True, autoincrement=True)
    sessionid = Column(BigInteger, nullable=False)  # Link do mdl_attendance_sessions
    studentid = Column(BigInteger, nullable=False)  # Link do mdl_user
    statusid = Column(BigInteger, nullable=False)  # Link do mdl_attendance_statuses
    statusset = Column(String(100), default="")  # Zestaw statusów aktywnych w danej sesji
    timetaken = Column(BigInteger, nullable=False)  # Unix timestamp wpisu
    takenby = Column(BigInteger, nullable=False)  # Kto zarejestrował obecność (ID użytkownika, np. wykładowca lub systemowy)
