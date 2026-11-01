from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator

Money = Decimal


class Login(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Register(Login):
    name: str = Field(min_length=2, max_length=120)
    company_name: str = Field(min_length=2, max_length=160)
    state_code: str = Field(pattern=r'^(0[1-9]|[12][0-9]|3[0-8])$')
    password: str = Field(min_length=12, max_length=128)


class CompanyInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    state_code: str = Field(pattern=r'^(0[1-9]|[12][0-9]|3[0-8])$')
    gstin: str | None = Field(default=None, pattern=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$')
    address: str = Field(default='', max_length=500)
    invoice_prefix: str = Field(default='INV', pattern=r'^[A-Z0-9-]{1,12}$')

    @field_validator('gstin',mode='before')
    @classmethod
    def empty_gstin(cls,value):
        return value or None


class CustomerInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr | None = None
    gstin: str | None = Field(default=None, pattern=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$')
    state_code: str = Field(pattern=r'^(0[1-9]|[12][0-9]|3[0-8])$')
    address: str = Field(default='', max_length=500)

    @field_validator('gstin','email',mode='before')
    @classmethod
    def empty_optional(cls,value):
        return value or None


class ProductInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    sku: str = Field(min_length=1, max_length=64)
    hsn: str = Field(pattern=r'^\d{4,8}$')
    unit: str = Field(default='NOS', min_length=1, max_length=20)
    price: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    gst_rate: Decimal = Field(ge=0, le=100, max_digits=9, decimal_places=4)
    is_service: bool = False
    active: bool = True


class InvoiceItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0, le=1000000, decimal_places=4)
    discount_percent: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    inclusive: bool = False


class DraftInput(BaseModel):
    customer_id: int = Field(gt=0)
    invoice_date: date
    due_date: date
    supply_state: str = Field(pattern=r'^(0[1-9]|[12][0-9]|3[0-8])$')
    supply_rule: Literal['domestic_standard', 'sez'] = 'domestic_standard'
    reverse_charge: bool = False
    items: list[InvoiceItem] = Field(min_length=1, max_length=200)

    @model_validator(mode='after')
    def dates(self):
        if self.due_date < self.invoice_date:
            raise ValueError('Due date cannot precede invoice date')
        return self


class PaymentInput(BaseModel):
    invoice_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    method: Literal['Cash', 'UPI', 'Bank transfer', 'Card', 'Cheque', 'Other']
    payment_date: date
    reference: str = Field(default='', max_length=100)
    idempotency_key: str = Field(min_length=16, max_length=64)


class CancelInput(BaseModel):
    reason: str = Field(min_length=10, max_length=500)


class MemberInput(BaseModel):
    email: EmailStr
    role: Literal['company_admin', 'accountant', 'billing_staff', 'inventory_manager', 'viewer']


class EmailActionInput(BaseModel):
    email: EmailStr


class ActionTokenInput(BaseModel):
    token: str = Field(min_length=32,max_length=128)


class ResetPasswordInput(ActionTokenInput):
    password: str = Field(min_length=12,max_length=72)
