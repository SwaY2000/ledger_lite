"""Account API routes."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from src.entities.account import AccountEntity
from src.presentation.rest.auth import get_current_account
from src.presentation.rest.v1.schemas.accounts.responses import AccountResponseSchema
from src.use_cases.dtos import AccountOutput, GetAccountInput
from src.use_cases.interfaces import IUseCase

from .api_docs import GET_ME_DOCS


__all__ = ('router',)


router = APIRouter(
    prefix='/accounts',
    tags=['Accounts'],
)


@router.get(
    path='/me',
    status_code=status.HTTP_200_OK,
    response_model=AccountResponseSchema,
    **GET_ME_DOCS,
)
@inject
async def get_me(
    account: AccountEntity = Depends(get_current_account),
    uc: IUseCase[GetAccountInput, AccountOutput] = Depends(Provide['get_account_use_case']),
) -> JSONResponse:
    """Return balances of the authenticated account.

    Args:
        account: Authenticated account
        uc: Injected use case for reading the account

    Returns:
        JSONResponse with USD and credits balances
    """
    result = await uc(GetAccountInput(account_id=account.ID))

    response_data = AccountResponseSchema(
        account_id=result.account_id,
        name=result.name,
        balance_usd=result.balance_usd,
        credits=result.credits,
    )
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_200_OK)
