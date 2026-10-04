"""Synthetic, isolated booking data; request policy is not a provider guarantee."""

from datetime import date, timedelta
from typing import Any, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingDates(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)
    checkin: date
    checkout: date

    @model_validator(mode="after")
    def checkout_follows_checkin(self) -> Self:
        if self.checkout <= self.checkin:
            raise ValueError("checkout must be after checkin")
        return self


class BookingRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)
    firstname: str = Field(min_length=1)
    lastname: str = Field(min_length=1)
    totalprice: int = Field(ge=0)
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: str


def booking_payload(
    *,
    total_price: int = 111,
    deposit_paid: bool = True,
    checkin: date | None = None,
    nights: int = 2,
) -> dict[str, Any]:
    if type(nights) is not int or nights <= 0:
        raise ValueError("nights must be a positive integer")
    arrival = date.today() + timedelta(days=14) if checkin is None else checkin
    model = BookingRequest(
        firstname="Portfolio",
        lastname=f"QA-{uuid4().hex}",
        totalprice=total_price,
        depositpaid=deposit_paid,
        bookingdates=BookingDates(checkin=arrival, checkout=arrival + timedelta(days=nights)),
        additionalneeds="Breakfast",
    )
    return model.model_dump(mode="json")
