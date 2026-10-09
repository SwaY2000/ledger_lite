"""Transaction history API routes."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from src.entities.account import AccountEntity
from src.presentation.rest.auth import get_current_account
from src.presentation.rest.v1.schemas.transactions.responses import TransactionItemSchema, TransactionListResponseSchema
from src.use_cases.dtos import ListTransactionsInput, ListTransactionsOutput
from src.use_cases.interfaces import IUseCase

from .api_docs import LIST_TRANSACTIONS_DOCS


__all__ = ('router',)


router = APIRouter(
    prefix='/transactions',
    tags=['Transactions'],
)


@router.get(
    path='',
    status_code=status.HTTP_200_OK,
    response_model=TransactionListResponseSchema,
    **LIST_TRANSACTIONS_DOCS,
)
@inject
async def list_transactions(
    limit: int = Query(20, ge=1, le=100, description='Page size'),
    cursor: str | None = Query(None, max_length=200, description='Cursor from the previous page'),
    account: AccountEntity = Depends(get_current_account),
    uc: IUseCase[ListTransactionsInput, ListTransactionsOutput] = Depends(Provide['list_transactions_use_case']),
) -> JSONResponse:
    """Return a page of the operation history.

    Args:
        limit: Page size
        cursor: Cursor from the previous page
        account: Authenticated account
        uc: Injected use case for the history

    Returns:
        JSONResponse with transactions and the next cursor
    """
    result = await uc(ListTransactionsInput(account_id=account.ID, limit=limit, cursor=cursor))

    response_data = TransactionListResponseSchema(
        items=[
            TransactionItemSchema(
                transaction_id=item.ID,
                type=item.type,
                amount_usd=item.amount_usd,
                credits=item.credits,
                reference_id=item.reference_id,
                counterparty_account_id=item.counterparty_account_id,
                created_at=item.created_at,
            )
            for item in result.items
        ],
        next_cursor=result.next_cursor,
    )
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_200_OK)
