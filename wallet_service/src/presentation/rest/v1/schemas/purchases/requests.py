"""Purchase request schemas."""

from pydantic import BaseModel, ConfigDict, Field, StrictInt


__all__ = ('CreatePurchaseRequestSchema',)


class CreatePurchaseRequestSchema(BaseModel):
    """Request schema for buying credits.

    Attributes:
        credits: Number of credits to buy
    """

    model_config = ConfigDict(extra='forbid')

    credits: StrictInt = Field(gt=0, le=1_000_000, description='Number of credits to buy', examples=[507])
