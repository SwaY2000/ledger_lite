from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    # common
    debug: bool = Field(validation_alias='DEBUG', default=False)
    env: str = Field(validation_alias='ENV', default='local')

    @computed_field
    def environment(self) -> Literal['local', 'development', 'staging', 'production', 'test']:
        if self.env == 'dev':
            return 'development'
        elif self.env == 'stage':
            return 'staging'
        elif self.env == 'prod':
            return 'production'
        elif self.env in ('local', 'test'):
            return self.env  # type: ignore[return-value]

        raise ValueError(f'Invalid ENV value: {self.env}')

    # postgres
    database_url: str = Field(validation_alias='DATABASE_URL')
    database_pool_size: int = Field(validation_alias='DATABASE_POOL_SIZE', default=10)
    database_max_overflow: int = Field(validation_alias='DATABASE_MAX_OVERFLOW', default=20)
    database_echo: bool = Field(validation_alias='DATABASE_ECHO', default=False)

    # payment provider
    provider_base_url: str = Field(validation_alias='PROVIDER_BASE_URL')
    provider_api_key: str = Field(validation_alias='PROVIDER_API_KEY')
    provider_webhook_secret: str = Field(validation_alias='PROVIDER_WEBHOOK_SECRET')
    provider_timeout_seconds: float = Field(validation_alias='PROVIDER_TIMEOUT_SECONDS', default=5.0)

    # wallet
    wallet_callback_url: str = Field(validation_alias='WALLET_CALLBACK_URL')
    webhook_tolerance_seconds: int = Field(validation_alias='WEBHOOK_TOLERANCE_SECONDS', default=300)

    # limiter
    rate_limit_per_minute: int = Field(validation_alias='RATE_LIMIT_PER_MINUTE', default=30)
    rate_limit_window_seconds: int = Field(validation_alias='RATE_LIMIT_WINDOW_SECONDS', default=60)

    # reconciliation
    reconcile_older_than_minutes: int = Field(validation_alias='RECONCILE_OLDER_THAN_MINUTES', default=15)
    reconcile_batch_size: int = Field(validation_alias='RECONCILE_BATCH_SIZE', default=100)


config = AppConfig()
