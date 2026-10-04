"""Session-per-request and a separate, read-only test oracle."""

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from framework_lab.models import Audit, Base, Document, User


def create_database(url: str):
    options = (
        {"connect_args": {"check_same_thread": False, "timeout": 15}}
        if url.startswith("sqlite")
        else {}
    )
    engine = create_engine(url, hide_parameters=True, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)


class DatabaseProbe:
    """Use returned IDs, never SQL string interpolation or service repository methods."""

    def __init__(self, engine):
        self.engine = engine

    def document(self, document_id: str) -> dict | None:
        with Session(self.engine) as db:
            row = db.get(Document, document_id)
            return (
                None
                if row is None
                else {
                    "id": row.id,
                    "owner_id": row.owner_id,
                    "tenant_id": row.tenant_id,
                    "sha256": row.sha256,
                    "size": row.size,
                    "content": row.content,
                }
            )

    def audit_events(self, user_id: str) -> list[str]:
        with Session(self.engine) as db:
            return list(db.scalars(select(Audit.event).where(Audit.user_id == user_id)))

    def password_is_hashed(self, user_id: str) -> bool:
        with Session(self.engine) as db:
            user = db.get(User, user_id)
            return user is not None and user.password_hash.startswith("$argon2id$")
