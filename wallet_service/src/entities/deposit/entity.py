"""Deposit entity module.

This module defines the DepositEntity class which represents a top-up of
an account through the external payment provider.
"""

from decimal import Decimal

from pydantic import Field

from src.entities.base import BaseEntity
from src.entities.money import calculate_net_deposit, calculate_provider_fee, quantize_cents

from .enums import DepositStatuses


__all__ = ('DepositEntity',)


class DepositEntity(BaseEntity):
    """Entity representing a deposit through the payment provider.

    Attributes:
        account_id: Account to be credited
        amount: Requested deposit amount
        status: Current deposit status
        invoice_id: Provider invoice identifier
        pay_url: Provider payment page URL
        paid_amount: Amount actually paid at the provider
        fee: Provider fee withheld from the paid amount
        credited_amount: Amount credited to the account (paid - fee)
    """

    account_id: str = Field(..., description='Account to be credited')
    amount: Decimal = Field(..., description='Requested deposit amount')
    status: DepositStatuses = Field(default=DepositStatuses.PENDING, description='Current deposit status')
    invoice_id: str | None = Field(default=None, description='Provider invoice identifier')
    pay_url: str | None = Field(default=None, description='Provider payment page URL')
    paid_amount: Decimal | None = Field(default=None, description='Amount actually paid at the provider')
    fee: Decimal | None = Field(default=None, description='Provider fee')
    credited_amount: Decimal | None = Field(default=None, description='Amount credited to the balance')

    @property
    def is_final(self) -> bool:
        """Whether the deposit is closed and must not change anymore."""
        return self.status.is_final

    def attach_invoice(self, invoice_id: str, pay_url: str) -> None:
        """Store provider invoice data after it was created.

        Args:
            invoice_id: Provider invoice identifier
            pay_url: Provider payment page URL
        """
        self.invoice_id = invoice_id
        self.pay_url = pay_url
        self.touch()

    def mark_failed(self) -> None:
        """Close the deposit because the provider invoice could not be created."""
        self.status = DepositStatuses.FAILED
        self.touch()

    def settle_paid(self, status: DepositStatuses, paid_amount: Decimal) -> Decimal:
        """Close the deposit as (partially) paid and compute the credited amount.

        Args:
            status: PAID or PARTIALLY_PAID
            paid_amount: Amount actually paid at the provider

        Returns:
            Amount to credit to the account (paid - fee)
        """
        paid = quantize_cents(paid_amount)
        self.status = status
        self.paid_amount = paid
        self.fee = calculate_provider_fee(paid)
        self.credited_amount = calculate_net_deposit(paid)
        self.touch()
        return self.credited_amount

    def expire(self) -> None:
        """Close the deposit without crediting the account."""
        self.status = DepositStatuses.EXPIRED
        self.paid_amount = Decimal('0.00')
        self.fee = Decimal('0.00')
        self.credited_amount = Decimal('0.00')
        self.touch()
