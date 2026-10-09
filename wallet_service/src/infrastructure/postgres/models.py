"""SQLAlchemy ORM models for the wallet service.

These models are the persistence representation of domain entities.
Monetary columns use NUMERIC(18, 2); balance invariants are additionally
enforced by CHECK constraints as a last line of defense.
"""

import datetime

from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


__all__ = (
    'Base',
    'AccountModel',
    'DepositModel',
    'TransactionModel',
    'IdempotencyKeyModel',
    'WebhookEventModel',
)

MONEY = Numeric(18, 2)

NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class Base(DeclarativeBase):
    """Declarative base with common columns and a naming convention."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))


class AccountModel(Base):
    """Persistence model of an account."""

    __tablename__ = 'accounts'
    __table_args__ = (
        CheckConstraint('balance_usd >= 0', name='balance_usd_non_negative'),
        CheckConstraint('credits >= 0', name='credits_non_negative'),
    )

    name: Mapped[str] = mapped_column(String(100))
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    balance_usd: Mapped[Decimal] = mapped_column(MONEY)
    credits: Mapped[int] = mapped_column(BigInteger)


class DepositModel(Base):
    """Persistence model of a deposit."""

    __tablename__ = 'deposits'
    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_positive'),
        Index('ix_deposits_status_created_at', 'status', 'created_at'),
    )

    account_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey('accounts.id'), index=True)
    amount: Mapped[Decimal] = mapped_column(MONEY)
    status: Mapped[str] = mapped_column(String(20))
    invoice_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    pay_url: Mapped[str | None] = mapped_column(Text)
    paid_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    fee: Mapped[Decimal | None] = mapped_column(MONEY)
    credited_amount: Mapped[Decimal | None] = mapped_column(MONEY)


class TransactionModel(Base):
    """Persistence model of a ledger transaction."""

    __tablename__ = 'transactions'
    __table_args__ = (Index('ix_transactions_account_id_created_at_id', 'account_id', 'created_at', 'id'),)

    account_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey('accounts.id'))
    type: Mapped[str] = mapped_column(String(20))
    amount_usd: Mapped[Decimal] = mapped_column(MONEY)
    credits: Mapped[int] = mapped_column(BigInteger)
    reference_id: Mapped[str | None] = mapped_column(String(64))
    counterparty_account_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False))


class IdempotencyKeyModel(Base):
    """Persistence model of a stored idempotent request."""

    __tablename__ = 'idempotency_keys'
    __table_args__ = (UniqueConstraint('account_id', 'key', name='uq_idempotency_keys_account_id_key'),)

    account_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey('accounts.id'))
    key: Mapped[str] = mapped_column(String(255))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class WebhookEventModel(Base):
    """Persistence model of a processed provider webhook event."""

    __tablename__ = 'webhook_events'

    event_id: Mapped[str] = mapped_column(String(64), unique=True)
    invoice_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20))
    paid_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    occurred_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
