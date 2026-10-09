"""Purchase API routes."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from src.entities.account import AccountEntity
from src.presentation.rest.auth import get_current_account
from src.presentation.rest.rate_limit import enforce_rate_limit
from src.presentation.rest.v1.schemas.purchases.requests import CreatePurchaseRequestSchema
from src.presentation.rest.v1.schemas.purchases.responses import PurchaseResponseSchema
from src.use_cases.dtos import CreatePurchaseInput, PurchaseOutput
from src.use_cases.interfaces import IUseCase

from .api_docs import CREATE_PURCHASE_DOCS


__all__ = ('router',)


router = APIRouter(
    prefix='/purchases',
    tags=['Purchases'],
)


@router.post(
    path='',
    status_code=status.HTTP_201_CREATED,
    response_model=PurchaseResponseSchema,
    dependencies=[Depends(enforce_rate_limit)],
    **CREATE_PURCHASE_DOCS,
)
@inject
async def create_purchase(
    data: CreatePurchaseRequestSchema,
    account: AccountEntity = Depends(get_current_account),
    uc: IUseCase[CreatePurchaseInput, PurchaseOutput] = Depends(Provide['create_purchase_use_case']),
) -> JSONResponse:
    """Buy credits with the USD balance.

    Args:
        data: Purchase request parameters
        account: Authenticated account
        uc: Injected use case for purchases

    Returns:
        JSONResponse with the charged price and updated balances
    """
    result = await uc(CreatePurchaseInput(account_id=account.ID, credits=data.credits))

    response_data = PurchaseResponseSchema(
        purchase_id=result.purchase_id,
        credits=result.credits,
        price_usd=result.price_usd,
        balance_usd=result.balance_usd,
        credits_balance=result.credits_balance,
        created_at=result.created_at,
    )
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_201_CREATED)
