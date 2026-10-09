"""Invoice API routes."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Security, status
from fastapi.responses import JSONResponse

from src.entities.invoice import InvoiceEntity, InvoiceStatuses
from src.presentation.rest.auth import is_valid_api_key_provided
from src.presentation.rest.schemas.invoices.requests import CreateInvoiceRequestSchema, SimulateInvoiceRequestSchema
from src.presentation.rest.schemas.invoices.responses import (
    CreateInvoiceResponseSchema,
    DeliverySchema,
    InvoiceResponseSchema,
    SimulateInvoiceResponseSchema,
)
from src.use_cases.dtos import (
    CreateInvoiceInput,
    CreateInvoiceOutput,
    GetInvoiceInput,
    SimulateInvoiceInput,
    SimulateInvoiceOutput,
)
from src.use_cases.interfaces import IUseCase

from .api_docs import CREATE_INVOICE_DOCS, GET_INVOICE_DOCS, SIMULATE_INVOICE_DOCS


__all__ = ('router',)


router = APIRouter(
    prefix='/invoices',
    tags=['Invoices'],
    dependencies=[Security(is_valid_api_key_provided)],
)


@router.post(
    path='',
    status_code=status.HTTP_201_CREATED,
    response_model=CreateInvoiceResponseSchema,
    **CREATE_INVOICE_DOCS,
)
@inject
async def create_invoice(
    data: CreateInvoiceRequestSchema,
    uc: IUseCase[CreateInvoiceInput, CreateInvoiceOutput] = Depends(Provide['create_invoice_use_case']),
) -> JSONResponse:
    """Create a pending invoice."""
    result = await uc(
        CreateInvoiceInput(
            amount=data.amount,
            currency=data.currency,
            external_id=data.external_id,
            callback_url=data.callback_url,
        ),
    )
    response_data = CreateInvoiceResponseSchema(
        invoice_id=result.invoice.ID,
        status=result.invoice.status,
        pay_url=result.pay_url,
    )
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_201_CREATED)


@router.get(
    path='/{invoice_id}',
    status_code=status.HTTP_200_OK,
    response_model=InvoiceResponseSchema,
    **GET_INVOICE_DOCS,
)
@inject
async def get_invoice(
    invoice_id: str,
    uc: IUseCase[GetInvoiceInput, InvoiceEntity] = Depends(Provide['get_invoice_use_case']),
) -> JSONResponse:
    """Return the current invoice state."""
    invoice = await uc(GetInvoiceInput(invoice_id=invoice_id))
    response_data = InvoiceResponseSchema.from_entity(invoice)
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_200_OK)


@router.post(
    path='/{invoice_id}/simulate',
    status_code=status.HTTP_200_OK,
    response_model=SimulateInvoiceResponseSchema,
    **SIMULATE_INVOICE_DOCS,
)
@inject
async def simulate_invoice(
    invoice_id: str,
    data: SimulateInvoiceRequestSchema,
    uc: IUseCase[SimulateInvoiceInput, SimulateInvoiceOutput] = Depends(Provide['simulate_invoice_use_case']),
) -> JSONResponse:
    """Move the invoice to a final status and deliver the webhook."""
    result = await uc(
        SimulateInvoiceInput(
            invoice_id=invoice_id,
            status=InvoiceStatuses(data.status),
            paid_amount=data.paid_amount,
            deliver_webhook=data.deliver_webhook,
            duplicate=data.duplicate,
        ),
    )
    invoice = InvoiceResponseSchema.from_entity(result.invoice)
    response_data = SimulateInvoiceResponseSchema(
        **invoice.model_dump(),
        event_id=result.event_id,
        deliveries=[DeliverySchema(status_code=d.status_code, error=d.error) for d in result.deliveries],
    )
    return JSONResponse(content=response_data.model_dump(mode='json'), status_code=status.HTTP_200_OK)
