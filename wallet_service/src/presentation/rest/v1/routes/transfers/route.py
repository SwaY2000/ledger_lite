"""Transfer API routes."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse

from src.entities.account import AccountEntity
from src.errors import IdempotencyKeyRequiredError
from src.presentation.rest.auth import get_current_account
from src.presentation.rest.rate_limit import enforce_rate_limit
from src.presentation.rest.v1.schemas.transfers.requests import CreateTransferRequestSchema
from src.presentation.rest.v1.schemas.transfers.responses import TransferResponseSchema
from src.use_cases.dtos import CreateTransferInput, CreateTransferOutput
from src.use_cases.interfaces import IUseCase

from .api_docs import CREATE_TRANSFER_DOCS


__all__ = ('router',)


router = APIRouter(
    prefix='/transfers',
    tags=['Transfers'],
)


@router.post(
    path='',
    status_code=status.HTTP_201_CREATED,
    response_model=TransferResponseSchema,
    dependencies=[Depends(enforce_rate_limit)],
    **CREATE_TRANSFER_DOCS,
)
@inject
async def create_transfer(
    data: CreateTransferRequestSchema,
    idempotency_key: str | None = Header(default=None, max_length=255),
    account: AccountEntity = Depends(get_current_account),
    uc: IUseCase[CreateTransferInput, CreateTransferOutput] = Depends(Provide['create_transfer_use_case']),
) -> JSONResponse:
    """Transfer money to another account exactly once per Idempotency-Key.

    Args:
        data: Transfer request parameters
        idempotency_key: Idempotency-Key header
        account: Authenticated account
        uc: Injected use case for transfers

    Returns:
        JSONResponse with the transfer result

    Raises:
        IdempotencyKeyRequiredError: 400 if the header is missing
    """
    if not idempotency_key:
        raise IdempotencyKeyRequiredError

    result = await uc(
        CreateTransferInput(
            account_id=account.ID,
            idempotency_key=idempotency_key,
            to_account_id=str(data.to_account_id),
            amount=data.amount,
        ),
    )

    transfer = result.transfer
    response_data = TransferResponseSchema(
        transfer_id=transfer.transfer_id,
        from_account_id=transfer.from_account_id,
        to_account_id=transfer.to_account_id,
        amount=transfer.amount,
        balance_usd=transfer.balance_usd,
        created_at=transfer.created_at,
    )
    return JSONResponse(
        content=response_data.model_dump(mode='json'),
        status_code=status.HTTP_201_CREATED,
        headers={'Idempotent-Replayed': 'true'} if result.replayed else None,
    )
