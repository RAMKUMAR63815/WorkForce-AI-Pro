# Generator type use pannrom; get_db() database session-ai yield pannum.
from collections.abc import Generator #Oru function yield use panni values provide pannum

# create_engine database connections manage panna use aagum.
from sqlalchemy import create_engine

# DeclarativeBase models-oda parent class.
# Session database operations handle pannum.
# sessionmaker database sessions create panna use aagum.
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Configuration file-la irundhu database settings edukkrom.
from app.core.config import get_settings


# Database host, username, password pondra settings load pannum.
settings = get_settings()


# MySQL database connections-ai manage panna engine create pannrom.
engine = create_engine(
    settings.database_url,  # Database connection details use pannum.

    pool_pre_ping=True,  # Connection alive-ah irukka check pannum.

    pool_size=5,  # Pool-la 5 connections retain panna configure pannum.

    max_overflow=10,  # Thevai adhigamaana nerathula 10 extra connections allow pannum.

    pool_recycle=1800,  # Connections-ai 30 minutes-kku piragu recycle panna configure pannum.
)


# Database sessions create panna reusable factory.
SessionLocal = sessionmaker(
    bind=engine,  # Indha sessions mela create panna engine-ai use pannum.

    class_=Session,  # SQLAlchemy Session class use pannum.

    autoflush=False,  # Query execute pannumbodhu pending changes automatic-ah flush aagadhu.

    expire_on_commit=False,  # Commit aanadhum loaded objects-oda attributes expire aagadhu.
)


# Ella database models-um indha Base class-ai inherit pannum.
class Base(DeclarativeBase):

    # Additional code inga thevai illa.
    # SQLAlchemy-oda model functionality inherit aagum.
    pass


# API request-kku database session provide panna function.
def get_db() -> Generator[Session, None, None]:

    # Pudhu database session create pannum.
    db = SessionLocal()

    try:
        # API endpoint indha session-ai use panna provide pannum.
        yield db

    finally:
        # Request mudinjaalum error vandhaalum session close aagum.
        db.close()