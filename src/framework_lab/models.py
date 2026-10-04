"""Small relational model, shared by SQLite development and PostgreSQL CI."""

from sqlalchemy import Boolean, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "lab_users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    tenant_id: Mapped[str] = mapped_column(String(36))
    role: Mapped[str] = mapped_column(String(16), default="member")
    mfa_method: Mapped[str] = mapped_column(String(8))
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_totp_step: Mapped[int] = mapped_column(Integer, default=-1)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[int] = mapped_column(Integer, default=0)


class Challenge(Base):
    __tablename__ = "lab_challenges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("lab_users.id", ondelete="CASCADE"))
    code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[int] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)


class AuthSession(Base):
    __tablename__ = "lab_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("lab_users.id", ondelete="CASCADE"))
    refresh_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[int] = mapped_column(Integer)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class RefreshToken(Base):
    __tablename__ = "lab_refresh_tokens"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("lab_sessions.id", ondelete="CASCADE"))
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class Document(Base):
    __tablename__ = "lab_documents"
    __table_args__ = (
        UniqueConstraint("owner_id", "idempotency_key", name="uq_lab_document_request"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("lab_users.id", ondelete="CASCADE"))
    tenant_id: Mapped[str] = mapped_column(String(36))
    filename: Mapped[str] = mapped_column(String(80))
    content_type: Mapped[str] = mapped_column(String(40))
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    idempotency_key: Mapped[str] = mapped_column(String(36))


class Audit(Base):
    __tablename__ = "lab_audit"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("lab_users.id", ondelete="CASCADE"))
    event: Mapped[str] = mapped_column(String(32))
    correlation_id: Mapped[str] = mapped_column(String(36))
