"""Purchase response schemas."""

import datetime

from pydantic import BaseModel, Field

from src.presentation.rest.v1.schemas.common import MoneyOut


__all__ = ('PurchaseResponseSchema',)


class PurchaseResponseSchema(BaseModel):
    """Response schema describing a credits purchase.

    Attributes:
        purchase_id: Purchase identifier
        credits: Purchased credits
        price_usd: Charged price
        balance_usd: USD balance after the purchase
        credits_balance: Credits balance after the purchase
        created_at: Purchase time
    """

    purchase_id: str = Field(description='Purchase identifier')
    credits: int = Field(description='Purchased credits', examples=[507])
    price_usd: MoneyOut = Field(description='Charged price', examples=['48.17'])
    balance_usd: MoneyOut = Field(description='USD balance after the purchase')
    credits_balance: int = Field(description='Credits balance after the purchase')
    created_at: datetime.datetime = Field(description='Purchase time')
