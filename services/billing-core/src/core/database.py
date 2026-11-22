"""Database engine, session management, and base declarative class."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import settings

# Configure SQLite or PostgreSQL engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that yields an active database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and seed demo farmer if not present."""
    from src.core.security import get_password_hash
    from src.models.db_models import User

    Base.metadata.create_all(bind=engine)

    # Seed demo farmer if database is empty
    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == "agricultor.picual@agroejemplo.es").first()
        if not existing:
            demo_farmer = User(
                email="agricultor.picual@agroejemplo.es",
                hashed_password=get_password_hash("PasswordSegura2026!"),
                name="Explotaciones Agrícolas San Isidro S.L.",
                cif_nif="B23987451",
                address="Finca Las Encinas, Parcela 12, 23400 Úbeda (Jaén)",
                regime="REAGP",
            )
            db.add(demo_farmer)
            db.commit()
