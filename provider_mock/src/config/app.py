from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    # common
    debug: bool = Field(validation_alias='DEBUG', default=False)
    env: str = Field(validation_alias='ENV', default='local')

    # provider
    provider_api_key: str = Field(validation_alias='PROVIDER_API_KEY')
    provider_webhook_secret: str = Field(validation_alias='PROVIDER_WEBHOOK_SECRET')
    provider_public_url: str = Field(validation_alias='PROVIDER_PUBLIC_URL', default='http://localhost:8081')

    # webhook delivery
    webhook_timeout_seconds: float = Field(validation_alias='WEBHOOK_TIMEOUT_SECONDS', default=5.0)


config = AppConfig()
