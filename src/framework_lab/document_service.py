"""Documents are stored transactionally with metadata in the owned lab database."""

import hashlib
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from framework_lab.auth_service import audit
from framework_lab.models import Document
from framework_lab.security import PolicyError, safe_filename


def document_view(row):
    return {
        key: getattr(row, key)
        for key in (
            "id",
            "owner_id",
            "tenant_id",
            "filename",
            "content_type",
            "sha256",
            "size",
        )
    }


class DocumentService:
    def __init__(self, settings):
        self.settings = settings

    def upload(self, db, user, filename, content_type, content, key, correlation_id):
        safe_filename(filename)
        if content_type != "text/plain":
            raise PolicyError(415, "unsupported_media")
        if not content or len(content) > self.settings.upload_limit:
            raise PolicyError(413, "invalid_file_size")
        try:
            content.decode("utf-8")
            if "\x00" in content.decode("utf-8"):
                raise ValueError
            UUID(key)
        except (UnicodeError, ValueError, TypeError):
            raise PolicyError(422, "invalid_document") from None
        fingerprint = hashlib.sha256(content).hexdigest()
        existing = db.scalar(
            select(Document).where(Document.owner_id == user.id, Document.idempotency_key == key)
        )
        if existing:
            return self._replay(existing, filename, content_type, fingerprint)
        row = Document(
            id=str(uuid4()),
            owner_id=user.id,
            tenant_id=user.tenant_id,
            filename=filename,
            content_type=content_type,
            sha256=fingerprint,
            size=len(content),
            content=content,
            idempotency_key=key,
        )
        db.add(row)
        try:
            db.flush()
            audit(db, user.id, "document_created", correlation_id)
            db.commit()
        except IntegrityError:
            db.rollback()
            # Concurrent same-key creation resolves via the DB uniqueness constraint.
            existing = db.scalar(
                select(Document).where(
                    Document.owner_id == user.id, Document.idempotency_key == key
                )
            )
            if existing is None:
                raise PolicyError(409, "document_conflict") from None
            return self._replay(existing, filename, content_type, fingerprint)
        return document_view(row), True

    def _replay(self, existing, filename, content_type, fingerprint):
        if (existing.filename, existing.content_type, existing.sha256) != (
            filename,
            content_type,
            fingerprint,
        ):
            raise PolicyError(409, "idempotency_conflict")
        return document_view(existing), False

    def owned(self, db, user, document_id):
        row = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == user.id,
                Document.tenant_id == user.tenant_id,
            )
        )
        if row is None:
            raise PolicyError(404, "document_not_found")
        return row
