"""Provider webhook event entity module.

Processed provider events are stored by their ``event_id`` to guarantee that
a redelivered webhook never credits money twice.
"""

import datetime

from decimal import Decimal

from pydantic import Field

from src.entities.base import BaseEntity


__all__ = ('WebhookEventEntity',)


class WebhookEventEntity(BaseEntity):
    """Entity representing a processed provider webhook event.

    Attributes:
        event_id: Provider event identifier (unique)
        invoice_id: Provider invoice identifier
        status: Invoice status reported by the event
        paid_amount: Paid amount reported by the event
        occurred_at: Time the event occurred at the provider
    """

    event_id: str = Field(..., description='Provider event identifier')
    invoice_id: str = Field(..., description='Provider invoice identifier')
    status: str = Field(..., description='Invoice status reported by the event')
    paid_amount: Decimal | None = Field(None, description='Paid amount reported by the event')
    occurred_at: datetime.datetime | None = Field(None, description='Time the event occurred at the provider')
