from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class AddressBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent Address ID (server-generated).",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"},
    )
    street: str = Field(
        ...,
        description="Street address and number.",
        json_schema_extra={"example": "123 Main St"},
    )
    city: str = Field(
        ...,
        description="City or locality.",
        json_schema_extra={"example": "New York"},
    )
    state: Optional[str] = Field(
        None,
        description="State/region code if applicable.",
        json_schema_extra={"example": "NY"},
    )
    postal_code: Optional[str] = Field(
        None,
        description="Postal or ZIP code.",
        json_schema_extra={"example": "10001"},
    )
    country: str = Field(
        ...,
        description="Country name or ISO label.",
        json_schema_extra={"example": "USA"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA",
                }
            ]
        }
    }


class AddressCreate(AddressBase):
    """Creation payload; ID is generated server-side but present in the base model."""
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "street": "221B Baker St",
                    "city": "London",
                    "state": None,
                    "postal_code": "NW1 6XE",
                    "country": "UK",
                }
            ]
        }
    }


class AddressUpdate(BaseModel):
    """Partial update; address ID is taken from the path, not the body."""
    street: Optional[str] = Field(
        None, description="Street address and number.", json_schema_extra={"example": "124 Main St"}
    )
    city: Optional[str] = Field(
        None, description="City or locality.", json_schema_extra={"example": "New York"}
    )
    state: Optional[str] = Field(
        None, description="State/region code if applicable.", json_schema_extra={"example": "NY"}
    )
    postal_code: Optional[str] = Field(
        None, description="Postal or ZIP code.", json_schema_extra={"example": "10002"}
    )
    country: Optional[str] = Field(
        None, description="Country name or ISO label.", json_schema_extra={"example": "USA"}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "street": "124 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10002",
                    "country": "USA",
                },
                {"city": "Brooklyn"},
            ]
        }
    }


class AddressRead(AddressBase):
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
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA",
                    "created_at": "2025-01-15T10:20:30Z",
                    "updated_at": "2025-01-16T12:00:00Z",
                }
            ]
        }
    }
