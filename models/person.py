from __future__ import annotations

from typing import Optional, List, Annotated
from uuid import UUID, uuid4
from datetime import date, datetime
from pydantic import BaseModel, Field, EmailStr, StringConstraints

from .address import AddressBase

# Columbia UNI: 2–3 lowercase letters + 1–4 digits (e.g., abc1234)
UNIType = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}\d{1,4}$")]


class PersonBase(BaseModel):
    uni: UNIType = Field(
        ...,
        description="Columbia University UNI (2–3 lowercase letters + 1–4 digits).",
        json_schema_extra={"example": "abc1234"},
    )
    first_name: str = Field(
        ...,
        description="Given name.",
        json_schema_extra={"example": "Ada"},
    )
    last_name: str = Field(
        ...,
        description="Family name.",
        json_schema_extra={"example": "Lovelace"},
    )
    email: EmailStr = Field(
        ...,
        description="Primary email address.",
        json_schema_extra={"example": "ada@example.com"},
    )
    phone: Optional[str] = Field(
        None,
        description="Contact phone number in any reasonable format.",
        json_schema_extra={"example": "+1-212-555-0199"},
    )
    birth_date: Optional[date] = Field(
        None,
        description="Date of birth (YYYY-MM-DD).",
        json_schema_extra={"example": "1815-12-10"},
    )

    # Embed addresses (each with persistent ID)
    addresses: List[AddressBase] = Field(
        default_factory=list,
        description="Addresses linked to this person (each carries a persistent Address ID).",
        json_schema_extra={
            "example": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "street": "123 Main St",
                    "city": "London",
                    "state": None,
                    "postal_code": "SW1A 1AA",
                    "country": "UK",
                }
            ]
        },
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "uni": "abc1234",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.com",
                    "phone": "+1-212-555-0199",
                    "birth_date": "1815-12-10",
                    "addresses": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "street": "123 Main St",
                            "city": "London",
                            "state": None,
                            "postal_code": "SW1A 1AA",
                            "country": "UK",
                        }
                    ],
                }
            ]
        }
    }


class PersonCreate(PersonBase):
    """Creation payload for a Person."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "uni": "xy123",
                    "first_name": "Grace",
                    "last_name": "Hopper",
                    "email": "grace.hopper@navy.mil",
                    "phone": "+1-202-555-0101",
                    "birth_date": "1906-12-09",
                    "addresses": [
                        {
                            "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                            "street": "1701 E St NW",
                            "city": "Washington",
                            "state": "DC",
                            "postal_code": "20552",
                            "country": "USA",
                        }
                    ],
                }
            ]
        }
    }


class PersonUpdate(BaseModel):
    """Partial update for a Person; supply only fields to change."""
    uni: Optional[UNIType] = Field(
        None, description="Columbia UNI.", json_schema_extra={"example": "ab1234"}
    )
    first_name: Optional[str] = Field(None, json_schema_extra={"example": "Augusta"})
    last_name: Optional[str] = Field(None, json_schema_extra={"example": "King"})
    email: Optional[EmailStr] = Field(None, json_schema_extra={"example": "ada@newmail.com"})
    phone: Optional[str] = Field(None, json_schema_extra={"example": "+44 20 7946 0958"})
    birth_date: Optional[date] = Field(None, json_schema_extra={"example": "1815-12-10"})
    addresses: Optional[List[AddressBase]] = Field(
        None,
        description="Replace the entire set of addresses with this list.",
        json_schema_extra={
            "example": [
                {
                    "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                    "street": "10 Downing St",
                    "city": "London",
                    "state": None,
                    "postal_code": "SW1A 2AA",
                    "country": "UK",
                }
            ]
        },
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"first_name": "Ada", "last_name": "Byron"},
                {"phone": "+1-415-555-0199"},
                {
                    "addresses": [
                        {
                            "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                            "street": "10 Downing St",
                            "city": "London",
                            "state": None,
                            "postal_code": "SW1A 2AA",
                            "country": "UK",
                        }
                    ]
                },
            ]
        }
    }


class PersonRead(PersonBase):
    """Server representation returned to clients."""
    id: UUID = Field(
        default_factory=uuid4,
        description="Server-generated Person ID.",
        json_schema_extra={"example": "99999999-9999-4999-8999-999999999999"},
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC).",
        json_schema_extra={"example": "2025-01-15T10:20:30Z"},
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC).",
        json_schema_extra={"example": "2025-01-16T12:00:00Z"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "99999999-9999-4999-8999-999999999999",
                    "uni": "abc1234",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.com",
                    "phone": "+1-212-555-0199",
                    "birth_date": "1815-12-10",
                    "addresses": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "street": "123 Main St",
                            "city": "London",
                            "state": None,
                            "postal_code": "SW1A 1AA",
                            "country": "UK",
                        }
                    ],
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }
