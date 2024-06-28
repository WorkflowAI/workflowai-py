from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from workflowai import Task
from workflowai.fields import Image


class MedicalInvoiceImageExtractionTaskInput(BaseModel):
    images: Optional[List[Image]] = Field(
        None,
        description="List of images of the medical invoices to be processed",
        min_length=1,
    )
    ocr_text: Optional[str] = Field(
        None,
        description="Optional raw OCR outputs that can be supplied",
        examples=["Raw OCR text from the invoice"],
    )


class IdentifierType(Enum):
    TIN = "TIN"
    EIN = "EIN"
    TPA = "TPA"


class Issuer(BaseModel):
    identifier: float = Field(
        description="Identifier of the issuer of the invoice", examples=[123456789]
    )
    name: str = Field(
        description="Name of the healthcare provider or facility",
        examples=["Healthcare Provider Inc."],
    )
    identifier_type: IdentifierType = Field(
        description="Type of identifier for the issuer", examples=["TIN"]
    )


class Recipient(BaseModel):
    identifier: str = Field(
        description="Patient identifier or account number", examples=["987654321"]
    )
    name: str = Field(
        description="Name on the invoice or insurance policy holder",
        examples=["John Doe"],
    )


class Status(Enum):
    ISSUED = "ISSUED"
    BALANCED = "BALANCED"
    CANCELLED = "CANCELLED"


class Subject(BaseModel):
    invoice_summary: str = Field(
        description="Summary of what the invoice is about",
        examples=["Routine Checkup and Lab Tests"],
    )
    invoice_title: str = Field(
        description="One line blurb generated that describes the invoice for display purposes",
        examples=["Invoice for Routine Checkup"],
    )


class BillingPeriod(BaseModel):
    start_date: datetime = Field(
        description="Start date of the billing period",
        examples=["2023-09-01T00:00:00Z"],
    )
    end_date: datetime = Field(
        description="End date of the billing period",
        examples=["2023-09-30T23:59:59Z"],
    )


class LineItemSystem(Enum):
    CPT = "CPT"
    ICD = "ICD"
    HCPCS = "HCPCS"
    OTHER = "OTHER"


class LineItemType(Enum):
    BASE = "BASE"
    DISCOUNT = "DISCOUNT"
    TAX = "TAX"


class LineItem(BaseModel):
    line_item_sequence: int = Field(
        description="Order of the line item on the invoice", examples=[1]
    )
    line_item_system: LineItemSystem = Field(
        description="The system that the code belongs to", examples=["CPT"]
    )
    line_item_code: str = Field(
        description="Specific code for the medical procedure or service",
        examples=["99213"],
    )
    line_item_service_description: str = Field(
        description="Description of the service provided",
        examples=["Office Visit"],
    )
    line_item_occurrence_date: datetime = Field(
        description="Date when the service was performed",
        examples=["2023-09-15T10:00:00Z"],
    )
    line_item_type: LineItemType = Field(
        description="Type of price component", examples=["BASE"]
    )
    line_item_amount: float = Field(
        description="Monetary amount of the price component", examples=[150]
    )


class IdentifierType1(Enum):
    NPI = "NPI"


class Practitioner(BaseModel):
    name: str = Field(
        description="Name of the practitioner who performed the service",
        examples=["Dr. Jane Smith"],
    )
    identifier: float = Field(
        description="Identifier of the practitioner who performed the service",
        examples=[1234567890],
    )
    identifier_type: IdentifierType1 = Field(
        description="Type of identifier for the practitioner", examples=["NPI"]
    )


class MedicalInvoiceImageExtractionTaskOutput(BaseModel):
    issuer: Issuer
    recipient: Recipient
    creation_date: datetime = Field(
        description="Date when the invoice was generated",
        examples=["2023-10-01T12:00:00Z"],
    )
    status: Status = Field(description="Status of the invoice", examples=["ISSUED"])
    isPaid: Optional[bool] = Field(
        None,
        description="Flag indicating if the invoice is paid",
        examples=[True, False],
    )
    subject: Subject
    billing_period: BillingPeriod
    invoice_identifier: str = Field(
        description="Unique identifier for the invoice", examples=["INV-123456"]
    )
    line_items: List[LineItem] = Field(
        description="Array of line items on the invoice", min_length=1
    )
    total_net_amount: float = Field(
        description="Total amount due after discounts, before taxes",
        examples=[150],
    )
    total_gross_amount: float = Field(
        description="Total amount due including taxes", examples=[165]
    )
    payment_notes: str = Field(
        description="Additional notes or comments related to the payment",
        examples=["Payment due within 30 days"],
    )
    payment_terms: str = Field(
        description="Terms of payment",
        examples=["Due date: 2023-10-31, Payment method: Credit Card"],
    )
    practitioner: Practitioner
    service_date: datetime = Field(
        description="Date when the service was performed",
        examples=["2023-09-15T10:00:00Z"],
    )


class MedicalInvoiceImageExtractionTask(
    Task[
        MedicalInvoiceImageExtractionTaskInput, MedicalInvoiceImageExtractionTaskOutput
    ]
):
    id: str = "medical-invoice-image-extraction"
    schema_id: int = 13
    input_class: type[MedicalInvoiceImageExtractionTaskInput] = (
        MedicalInvoiceImageExtractionTaskInput
    )
    output_class: type[MedicalInvoiceImageExtractionTaskOutput] = (
        MedicalInvoiceImageExtractionTaskOutput
    )
