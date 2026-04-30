from sqlalchemy import create_engine, Column, String, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Zastąp rzeczywistymi danymi: mysql+pymysql://użytkownik:hasło@host:port/nazwa_bazy
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/twoja_baza"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Przykład modelu tabeli - dostosuj nazwy do danej bazy!
class User(Base):
    __tablename__ = "uzytkownicy"
    id = Column(BigInteger, primary_key=True, index=True)
    auth = Column(String(20))
    confirmed = Column(Boolean)
    policyagreed = Column(Boolean)
    deleted = Column(Boolean)
    suspended = Column(Boolean)
    mnethostid = Column(BigInteger)
    username = Column(String(100))
    password = Column(String(255))
    idnumber = Column(String(255))
    firstname = Column(String(100))