"""Account response schemas."""

from pydantic import BaseModel, Field

from src.presentation.rest.v1.schemas.common import MoneyOut


__all__ = ('AccountResponseSchema',)


class AccountResponseSchema(BaseModel):
    """Response schema with account balances.

    Attributes:
        account_id: Account identifier
        name: Account name
        balance_usd: USD balance as a decimal string
        credits: Credits balance
    """

    account_id: str = Field(description='Account identifier', examples=['0b0c3f5e-8b1e-4bb5-8a39-2f1f0b6f4f0e'])
    name: str = Field(description='Account name', examples=['alice'])
    balance_usd: MoneyOut = Field(description='USD balance')
    credits: int = Field(description='Credits balance', examples=[507])
