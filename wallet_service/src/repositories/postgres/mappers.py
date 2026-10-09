"""Entity-model mappers for PostgreSQL persistence.

This module provides mapping functionality between domain entities and
SQLAlchemy models, handling enum conversions and field naming differences
between the domain and persistence layers.
"""

from src.entities.account import AccountEntity
from src.entities.deposit import DepositEntity, DepositStatuses
from src.entities.idempotency import IdempotencyRecordEntity
from src.entities.transaction import TransactionEntity, TransactionTypes
from src.entities.webhook_event import WebhookEventEntity
from src.infrastructure.postgres.models import (
    AccountModel,
    DepositModel,
    IdempotencyKeyModel,
    TransactionModel,
    WebhookEventModel,
)


__all__ = (
    'AccountMapper',
    'DepositMapper',
    'TransactionMapper',
    'IdempotencyRecordMapper',
    'WebhookEventMapper',
)


class AccountMapper:
    """Mapper between AccountEntity and AccountModel."""

    def to_model(self, entity: AccountEntity) -> AccountModel:
        """Convert AccountEntity to its persistence model."""
        return AccountModel(
            id=entity.ID,
            name=entity.name,
            api_key_hash=entity.api_key_hash,
            balance_usd=entity.balance_usd,
            credits=entity.credits,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self, model: AccountModel) -> AccountEntity:
        """Convert AccountModel to the domain entity."""
        return AccountEntity(
            ID=model.id,
            name=model.name,
            api_key_hash=model.api_key_hash,
            balance_usd=model.balance_usd,
            credits=model.credits,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class DepositMapper:
    """Mapper between DepositEntity and DepositModel."""

    def to_model(self, entity: DepositEntity) -> DepositModel:
        """Convert DepositEntity to its persistence model."""
        return DepositModel(
            id=entity.ID,
            account_id=entity.account_id,
            amount=entity.amount,
            status=entity.status.value,
            invoice_id=entity.invoice_id,
            pay_url=entity.pay_url,
            paid_amount=entity.paid_amount,
            fee=entity.fee,
            credited_amount=entity.credited_amount,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self, model: DepositModel) -> DepositEntity:
        """Convert DepositModel to the domain entity."""
        return DepositEntity(
            ID=model.id,
            account_id=model.account_id,
            amount=model.amount,
            status=DepositStatuses(model.status),
            invoice_id=model.invoice_id,
            pay_url=model.pay_url,
            paid_amount=model.paid_amount,
            fee=model.fee,
            credited_amount=model.credited_amount,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class TransactionMapper:
    """Mapper between TransactionEntity and TransactionModel."""

    def to_model(self, entity: TransactionEntity) -> TransactionModel:
        """Convert TransactionEntity to its persistence model."""
        return TransactionModel(
            id=entity.ID,
            account_id=entity.account_id,
            type=entity.type.value,
            amount_usd=entity.amount_usd,
            credits=entity.credits,
            reference_id=entity.reference_id,
            counterparty_account_id=entity.counterparty_account_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self, model: TransactionModel) -> TransactionEntity:
        """Convert TransactionModel to the domain entity."""
        return TransactionEntity(
            ID=model.id,
            account_id=model.account_id,
            type=TransactionTypes(model.type),
            amount_usd=model.amount_usd,
            credits=model.credits,
            reference_id=model.reference_id,
            counterparty_account_id=model.counterparty_account_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class IdempotencyRecordMapper:
    """Mapper between IdempotencyRecordEntity and IdempotencyKeyModel."""

    def to_model(self, entity: IdempotencyRecordEntity) -> IdempotencyKeyModel:
        """Convert IdempotencyRecordEntity to its persistence model."""
        return IdempotencyKeyModel(
            id=entity.ID,
            account_id=entity.account_id,
            key=entity.key,
            request_hash=entity.request_hash,
            response_status=entity.response_status,
            response_body=entity.response_body,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self, model: IdempotencyKeyModel) -> IdempotencyRecordEntity:
        """Convert IdempotencyKeyModel to the domain entity."""
        return IdempotencyRecordEntity(
            ID=model.id,
            account_id=model.account_id,
            key=model.key,
            request_hash=model.request_hash,
            response_status=model.response_status,
            response_body=model.response_body,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class WebhookEventMapper:
    """Mapper between WebhookEventEntity and WebhookEventModel."""

    def to_model(self, entity: WebhookEventEntity) -> WebhookEventModel:
        """Convert WebhookEventEntity to its persistence model."""
        return WebhookEventModel(
            id=entity.ID,
            event_id=entity.event_id,
            invoice_id=entity.invoice_id,
            status=entity.status,
            paid_amount=entity.paid_amount,
            occurred_at=entity.occurred_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self, model: WebhookEventModel) -> WebhookEventEntity:
        """Convert WebhookEventModel to the domain entity."""
        return WebhookEventEntity(
            ID=model.id,
            event_id=model.event_id,
            invoice_id=model.invoice_id,
            status=model.status,
            paid_amount=model.paid_amount,
            occurred_at=model.occurred_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
