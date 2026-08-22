from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        engine_options: dict[str, object] = {"pool_pre_ping": True}
        if settings.database_url.startswith("sqlite"):
            engine_options.update(
                {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
            )
        self.engine: Engine = create_engine(settings.database_url, **engine_options)
        self.session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=False
        )

    def session(self) -> Session:
        return self.session_factory()
