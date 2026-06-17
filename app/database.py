from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Tworzenie silnika połączeń
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Pomaga radzić sobie z zerwanymi połączeniami
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Generator sesji bazy danych (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
