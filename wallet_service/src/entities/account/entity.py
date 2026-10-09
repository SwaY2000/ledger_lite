"""Account entity module.

This module defines the AccountEntity class which represents a user's
internal account with a USD balance and a credits balance.
"""

from decimal import Decimal

from pydantic import Field

from src.entities.base import BaseEntity
from src.entities.money import quantize_cents
from src.errors import InsufficientFundsError


__all__ = ('AccountEntity',)


class AccountEntity(BaseEntity):
    """Entity representing a user account.

    The entity owns the balance invariants: the USD balance is stored with
    cent precision and can never become negative.

    Attributes:
        name: Human-readable account name
        api_key_hash: SHA-256 hash of the account API key (plain key is never stored)
        balance_usd: Current USD balance
        credits: Current credits balance
    """

    name: str = Field(..., description='Human-readable account name')
    api_key_hash: str = Field(..., description='SHA-256 hash of the API key')
    balance_usd: Decimal = Field(default=Decimal('0.00'), description='USD balance with cent precision')
    credits: int = Field(default=0, description='Credits balance')

    def credit(self, amount: Decimal) -> None:
        """Add money to the USD balance.

        Args:
            amount: Positive amount to add
        """
        self.balance_usd = quantize_cents(self.balance_usd + amount)
        self.touch()

    def debit(self, amount: Decimal) -> None:
        """Withdraw money from the USD balance.

        Args:
            amount: Positive amount to withdraw

        Raises:
            InsufficientFundsError: If the balance is lower than the amount
        """
        if self.balance_usd < amount:
            raise InsufficientFundsError(
                details={
                    'balance_usd': f'{self.balance_usd:.2f}',
                    'required_usd': f'{amount:.2f}',
                },
            )
        self.balance_usd = quantize_cents(self.balance_usd - amount)
        self.touch()

    def add_credits(self, quantity: int) -> None:
        """Add purchased credits to the credits balance.

        Args:
            quantity: Positive number of credits
        """
        self.credits += quantity
        self.touch()
