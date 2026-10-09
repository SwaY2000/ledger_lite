"""Provider webhook API routes."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse

from src.presentation.rest.v1.schemas.webhooks.responses import WebhookResponseSchema
from src.use_cases.dtos import ProcessProviderWebhookInput, ProcessProviderWebhookOutput
from src.use_cases.interfaces import IUseCase

from .api_docs import PROVIDER_WEBHOOK_DOCS


__all__ = ('router',)


router = APIRouter(
    prefix='/webhooks',
    tags=['Webhooks'],
)


@router.post(
    path='/provider',
    status_code=status.HTTP_200_OK,
    response_model=WebhookResponseSchema,
    **PROVIDER_WEBHOOK_DOCS,
)
@inject
async def provider_webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    x_timestamp: str | None = Header(default=None),
    uc: IUseCase[ProcessProviderWebhookInput, ProcessProviderWebhookOutput] = Depends(
        Provide['process_provider_webhook_use_case'],
    ),
) -> JSONResponse:
    """Process a signed webhook from the payment provider.

    The raw body is passed through untouched because the signature is
    computed over the exact bytes sent by the provider.

    Args:
        request: Incoming request (raw body is read from it)
        x_signature: X-Signature header
        x_timestamp: X-Timestamp header
        uc: Injected webhook processing use case

    Returns:
        JSONResponse acknowledging the event
    """
    result = await uc(
        ProcessProviderWebhookInput(
            raw_body=await request.body(),
            signature=x_signature,
            timestamp=x_timestamp,
        ),
    )

    response_data = WebhookResponseSchema(result=result.result, deposit_id=result.deposit_id)
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_200_OK)
