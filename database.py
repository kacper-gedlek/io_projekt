import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, BigInteger, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "mdl_user"

    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(100))
    idnumber = Column(String(255))
    firstname = Column(String(100))
    lastname = Column(String(100))
    email = Column(String(100))
    confirmed = Column(Boolean)
    suspended = Column(Boolean)
    lastaccess = Column(BigInteger)
    department = Column(String(200))


class Course(Base):
    __tablename__ = "mdl_course"

    id = Column(Integer, primary_key=True)
    fullname = Column(String(254))
    shortname = Column(String(255))