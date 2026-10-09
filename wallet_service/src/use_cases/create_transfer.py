"""Use case for idempotent transfers between accounts."""

import hashlib
import json

from uuid import uuid4

from src.entities.base import utc_now
from src.entities.idempotency import IdempotencyRecordEntity
from src.entities.money import format_money
from src.entities.transaction import TransactionEntity, TransactionTypes
from src.errors import AccountNotFoundError, IdempotencyKeyConflictError, InvalidTransferError
from src.repositories.interfaces import IUnitOfWork

from .dtos import CreateTransferInput, CreateTransferOutput, TransferResult


__all__ = ('CreateTransferUseCase',)


class CreateTransferUseCase:
    """Use case moving money between two accounts exactly once per Idempotency-Key.

    Everything happens in one transaction:

    1. Insert the idempotency record. A concurrent request with the same key
       blocks on the unique index until the first one commits or rolls back.
    2. If the key exists: same body -> replay the stored result,
       different body -> 409.
    3. Lock both accounts (ascending id order, no deadlocks), check the
       balance, move money, write two ledger rows and store the result.

    Business errors roll the transaction back, including the idempotency
    record, so a failed attempt (e.g. insufficient funds) can be retried
    with the same key once the balance allows it.
    """

    def __init__(self, uow: IUnitOfWork) -> None:
        """Initialize the use case with required dependencies."""
        self._uow = uow

    @staticmethod
    def _request_hash(request: CreateTransferInput) -> str:
        """Hash the canonical request body for idempotency comparison."""
        canonical = json.dumps(
            {'to_account_id': request.to_account_id, 'amount': format_money(request.amount)},
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def __call__(self, request: CreateTransferInput) -> CreateTransferOutput:
        """Execute an idempotent transfer.

        Args:
            request: Input DTO with sender, recipient, amount and Idempotency-Key

        Returns:
            Transfer result (``replayed=True`` for a repeated key)

        Raises:
            IdempotencyKeyConflictError: Key reused with a different body (409)
            InvalidTransferError: Transfer to the same account (400)
            AccountNotFoundError: Recipient does not exist (404)
            InsufficientFundsError: Balance too low (409)
        """
        if request.to_account_id == request.account_id:
            raise InvalidTransferError('Cannot transfer to the same account')

        request_hash = self._request_hash(request)

        async with self._uow:
            record = IdempotencyRecordEntity(
                account_id=request.account_id,
                key=request.idempotency_key,
                request_hash=request_hash,
            )
            if not await self._uow.idempotency.try_create(record):
                existing = await self._uow.idempotency.get(request.account_id, request.idempotency_key)
                if existing is None or existing.request_hash != request_hash or existing.response_body is None:
                    raise IdempotencyKeyConflictError
                return CreateTransferOutput(transfer=TransferResult.from_dict(existing.response_body), replayed=True)

            accounts = await self._uow.accounts.lock_many([request.account_id, request.to_account_id])
            sender = accounts.get(request.account_id)
            recipient = accounts.get(request.to_account_id)
            if sender is None or recipient is None:
                raise AccountNotFoundError(details={'account_id': request.to_account_id})

            sender.debit(request.amount)
            recipient.credit(request.amount)
            await self._uow.accounts.update(sender)
            await self._uow.accounts.update(recipient)

            transfer_id = str(uuid4())
            created_at = utc_now()
            await self._uow.transactions.create(
                TransactionEntity(
                    account_id=sender.ID,
                    type=TransactionTypes.TRANSFER_OUT,
                    amount_usd=-request.amount,
                    reference_id=transfer_id,
                    counterparty_account_id=recipient.ID,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            )
            await self._uow.transactions.create(
                TransactionEntity(
                    account_id=recipient.ID,
                    type=TransactionTypes.TRANSFER_IN,
                    amount_usd=request.amount,
                    reference_id=transfer_id,
                    counterparty_account_id=sender.ID,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            )

            result = TransferResult(
                transfer_id=transfer_id,
                from_account_id=sender.ID,
                to_account_id=recipient.ID,
                amount=request.amount,
                balance_usd=sender.balance_usd,
                created_at=created_at,
            )
            record.store_response(201, result.to_dict())
            await self._uow.idempotency.update(record)
            await self._uow.commit()

        return CreateTransferOutput(transfer=result)
