"""Deposit API routes."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from src.entities.account import AccountEntity
from src.presentation.rest.auth import get_current_account
from src.presentation.rest.rate_limit import enforce_rate_limit
from src.presentation.rest.v1.schemas.deposits.requests import CreateDepositRequestSchema
from src.presentation.rest.v1.schemas.deposits.responses import DepositResponseSchema
from src.use_cases.dtos import CreateDepositInput, DepositOutput
from src.use_cases.interfaces import IUseCase

from .api_docs import CREATE_DEPOSIT_DOCS


__all__ = ('router',)


router = APIRouter(
    prefix='/deposits',
    tags=['Deposits'],
)


@router.post(
    path='',
    status_code=status.HTTP_201_CREATED,
    response_model=DepositResponseSchema,
    dependencies=[Depends(enforce_rate_limit)],
    **CREATE_DEPOSIT_DOCS,
)
@inject
async def create_deposit(
    data: CreateDepositRequestSchema,
    account: AccountEntity = Depends(get_current_account),
    uc: IUseCase[CreateDepositInput, DepositOutput] = Depends(Provide['create_deposit_use_case']),
) -> JSONResponse:
    """Create a deposit and a provider invoice.

    Args:
        data: Deposit request parameters
        account: Authenticated account
        uc: Injected use case for deposit creation

    Returns:
        JSONResponse with the pending deposit and its pay_url
    """
    result = await uc(CreateDepositInput(account_id=account.ID, amount=data.amount))

    response_data = DepositResponseSchema(
        deposit_id=result.deposit_id,
        status=result.status,
        amount=result.amount,
        invoice_id=result.invoice_id,
        pay_url=result.pay_url,
        created_at=result.created_at,
    )
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_201_CREATED)
