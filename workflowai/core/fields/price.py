from enum import Enum

from pydantic import BaseModel, Field


class Currency(Enum):
    USD = "USD"  # United States Dollar
    EUR = "EUR"  # Euro
    JPY = "JPY"  # Japanese Yen
    GBP = "GBP"  # British Pound Sterling
    AUD = "AUD"  # Australian Dollar
    CAD = "CAD"  # Canadian Dollar
    CHF = "CHF"  # Swiss Franc
    CNY = "CNY"  # Chinese Yuan Renminbi
    SEK = "SEK"  # Swedish Krona
    NZD = "NZD"  # New Zealand Dollar
    MXN = "MXN"  # Mexican Peso
    SGD = "SGD"  # Singapore Dollar
    HKD = "HKD"  # Hong Kong Dollar
    NOK = "NOK"  # Norwegian Krone
    KRW = "KRW"  # South Korean Won
    TRY = "TRY"  # Turkish Lira
    INR = "INR"  # Indian Rupee
    RUB = "RUB"  # Russian Ruble
    BRL = "BRL"  # Brazilian Real
    ZAR = "ZAR"  # South African Rand
    DKK = "DKK"  # Danish Krone
    PLN = "PLN"  # Polish Zloty
    THB = "THB"  # Thai Baht
    IDR = "IDR"  # Indonesian Rupiah
    MYR = "MYR"  # Malaysian Ringgit
    # Those are 25 of the most common currencies in the world.
    # You can duplicate this object add more if you need to or contact support@workflowai.com
    # to add more currencies to the list.


class Price(BaseModel):
    amount: float = Field(description="The amount of the price.", examples=[250000.0])
    currency: Currency = Field(
        description="The currency of the price.",
        examples=["USD", "EUR"],
    )
