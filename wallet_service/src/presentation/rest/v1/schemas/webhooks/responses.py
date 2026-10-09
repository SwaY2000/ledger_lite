"""Provider webhook response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


__all__ = ('WebhookResponseSchema',)


class WebhookResponseSchema(BaseModel):
    """Acknowledgement returned to the provider.

    Attributes:
        result: processed, duplicate or ignored
        deposit_id: Affected deposit identifier
    """

    result: Literal['processed', 'duplicate', 'ignored'] = Field(
        description='processed: deposit closed by this event; duplicate: event already processed; '
        'ignored: deposit already closed or still pending',
        examples=['processed'],
    )
    deposit_id: str | None = Field(default=None, description='Affected deposit identifier')
