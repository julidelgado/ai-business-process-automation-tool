from app.db.session import engine
from app.models import entities  # noqa: F401
from app.models.entities import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
