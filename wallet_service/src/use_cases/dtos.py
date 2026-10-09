"""Data Transfer Objects (DTOs) for use case inputs and outputs.

This module defines the data structures used for input and output
of use case operations. DTOs provide clear contracts for data
exchange between the presentation layer and business logic.
"""

import datetime

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from src.entities.account import AccountEntity
from src.entities.deposit import DepositStatuses
from src.entities.money import format_money
from src.entities.transaction import TransactionEntity


__all__ = (
    'CreateAccountInput',
    'CreateAccountOutput',
    'AuthenticateAccountInput',
    'GetAccountInput',
    'AccountOutput',
    'CreateDepositInput',
    'DepositOutput',
    'ProcessProviderWebhookInput',
    'ProcessProviderWebhookOutput',
    'CreateTransferInput',
    'TransferResult',
    'CreateTransferOutput',
    'CreatePurchaseInput',
    'PurchaseOutput',
    'ListTransactionsInput',
    'ListTransactionsOutput',
    'ReconcileDepositsInput',
    'ReconcileDepositsOutput',
)


@dataclass
class CreateAccountInput:
    """Input DTO for account creation.

    Attributes:
        name: Human-readable account name
    """

    name: str


@dataclass
class CreateAccountOutput:
    """Output DTO for account creation.

    Attributes:
        account_id: Identifier of the created account
        name: Account name
        api_key: Plain API key (returned only once, never stored)
    """

    account_id: str
    name: str
    api_key: str


@dataclass
class AuthenticateAccountInput:
    """Input DTO for API key authentication.

    Attributes:
        api_key: Plain API key from the X-API-Key header
    """

    api_key: str | None


@dataclass
class GetAccountInput:
    """Input DTO for reading an account.

    Attributes:
        account_id: Account identifier
    """

    account_id: str


@dataclass
class AccountOutput:
    """Output DTO describing account balances.

    Attributes:
        account_id: Account identifier
        name: Account name
        balance_usd: USD balance
        credits: Credits balance
    """

    account_id: str
    name: str
    balance_usd: Decimal
    credits: int

    @classmethod
    def from_entity(cls, account: AccountEntity) -> 'AccountOutput':
        """Build the DTO from an account entity."""
        return cls(account_id=account.ID, name=account.name, balance_usd=account.balance_usd, credits=account.credits)


@dataclass
class CreateDepositInput:
    """Input DTO for deposit creation.

    Attributes:
        account_id: Account to be credited
        amount: Requested deposit amount
    """

    account_id: str
    amount: Decimal


@dataclass
class DepositOutput:
    """Output DTO describing a deposit.

    Attributes:
        deposit_id: Deposit identifier
        status: Deposit status
        amount: Requested amount
        invoice_id: Provider invoice identifier
        pay_url: Provider payment page URL
        created_at: Creation time
    """

    deposit_id: str
    status: DepositStatuses
    amount: Decimal
    invoice_id: str | None
    pay_url: str | None
    created_at: datetime.datetime


@dataclass
class ProcessProviderWebhookInput:
    """Input DTO for provider webhook processing.

    Attributes:
        raw_body: Exact request body bytes (signature is computed over them)
        signature: X-Signature header value
        timestamp: X-Timestamp header value
    """

    raw_body: bytes
    signature: str | None
    timestamp: str | None


@dataclass
class ProcessProviderWebhookOutput:
    """Output DTO for provider webhook processing.

    Attributes:
        result: ``processed`` if the deposit was closed by this event,
            ``duplicate`` if the event was already processed,
            ``ignored`` if the deposit was already closed or is still pending
        deposit_id: Affected deposit identifier
    """

    result: Literal['processed', 'duplicate', 'ignored']
    deposit_id: str | None = None


@dataclass
class CreateTransferInput:
    """Input DTO for transfer creation.

    Attributes:
        account_id: Sender account
        idempotency_key: Client-provided Idempotency-Key
        to_account_id: Recipient account
        amount: Amount to transfer
    """

    account_id: str
    idempotency_key: str
    to_account_id: str
    amount: Decimal


@dataclass
class TransferResult:
    """Result of a completed transfer, stored for idempotent replays.

    Attributes:
        transfer_id: Transfer identifier
        from_account_id: Sender account
        to_account_id: Recipient account
        amount: Transferred amount
        balance_usd: Sender balance right after the transfer
        created_at: Transfer time
    """

    transfer_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    balance_usd: Decimal
    created_at: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            'transfer_id': self.transfer_id,
            'from_account_id': self.from_account_id,
            'to_account_id': self.to_account_id,
            'amount': format_money(self.amount),
            'balance_usd': format_money(self.balance_usd),
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'TransferResult':
        """Deserialize from a dict produced by ``to_dict``."""
        return cls(
            transfer_id=data['transfer_id'],
            from_account_id=data['from_account_id'],
            to_account_id=data['to_account_id'],
            amount=Decimal(data['amount']),
            balance_usd=Decimal(data['balance_usd']),
            created_at=datetime.datetime.fromisoformat(data['created_at']),
        )


@dataclass
class CreateTransferOutput:
    """Output DTO for transfer creation.

    Attributes:
        transfer: Transfer result
        replayed: True if the result was replayed for a repeated Idempotency-Key
    """

    transfer: TransferResult
    replayed: bool = False


@dataclass
class CreatePurchaseInput:
    """Input DTO for credits purchase.

    Attributes:
        account_id: Buyer account
        credits: Number of credits to buy
    """

    account_id: str
    credits: int


@dataclass
class PurchaseOutput:
    """Output DTO for credits purchase.

    Attributes:
        purchase_id: Purchase identifier
        credits: Purchased credits
        price_usd: Charged price
        balance_usd: USD balance after the purchase
        credits_balance: Credits balance after the purchase
        created_at: Purchase time
    """

    purchase_id: str
    credits: int
    price_usd: Decimal
    balance_usd: Decimal
    credits_balance: int
    created_at: datetime.datetime


@dataclass
class ListTransactionsInput:
    """Input DTO for the operation history.

    Attributes:
        account_id: Account identifier
        limit: Page size
        cursor: Opaque cursor returned by the previous page
    """

    account_id: str
    limit: int = 20
    cursor: str | None = None


@dataclass
class ListTransactionsOutput:
    """Output DTO for the operation history.

    Attributes:
        items: Transactions, newest first
        next_cursor: Cursor of the next page (None on the last page)
    """

    items: list[TransactionEntity]
    next_cursor: str | None = None


@dataclass
class ReconcileDepositsInput:
    """Input DTO for pending deposits reconciliation.

    Attributes:
        older_than_minutes: Only deposits pending longer than this are checked
        limit: Maximum number of deposits per run
    """

    older_than_minutes: int
    limit: int = 100


@dataclass
class ReconcileDepositsOutput:
    """Output DTO for pending deposits reconciliation.

    Attributes:
        checked: Number of deposits checked at the provider
        settled: Number of deposits closed by this run
        still_pending: Number of deposits still pending at the provider
        errors: Deposit ids that could not be reconciled, with reasons
    """

    checked: int = 0
    settled: int = 0
    still_pending: int = 0
    errors: dict[str, str] = field(default_factory=dict)
