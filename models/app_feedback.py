# app_feedback.py
"""
Schemas for app-level feedback in the Feedback microservice.

Layered Pydantic models:
- AppFeedbackBase: shared domain fields (no id/timestamps)
- AppFeedbackCreate: payload required to create feedback
- AppFeedbackUpdate: partial update (PATCH)
- AppFeedbackOut: read model including id and timestamps

Notes:
- No platform, app_version, moderation, or device/OS context per product spec.
- Ratings are 1..5; only `overall` is required.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


# -------------------------------
# Shared domain (no ids/dates)
# -------------------------------

class AppFeedbackBase(BaseModel):
    # Author (optional if allowing anonymous or external capture flows)
    author_profile_id: Optional[UUID] = Field(
        None, description="Profile leaving the feedback (optional)"
    )

    # Ratings
    overall: int = Field(
        ..., ge=1, le=5, description="Required overall rating from 1 (worst) to 5 (best)"
    )
    usability: Optional[int] = Field(
        None, ge=1, le=5, description="Optional usability rating (1..5)"
    )
    reliability: Optional[int] = Field(
        None, ge=1, le=5, description="Optional reliability rating (1..5)"
    )
    performance: Optional[int] = Field(
        None, ge=1, le=5, description="Optional performance rating (1..5)"
    )
    support_experience: Optional[int] = Field(
        None, ge=1, le=5, description="Optional support experience rating (1..5)"
    )

    # Qualitative
    headline: Optional[str] = Field(
        None, min_length=1, max_length=120, description="Optional short title"
    )
    comment: Optional[str] = Field(
        None, min_length=1, max_length=2000, description="Optional free-text comment"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description='Optional tags (e.g., "bug", "feature-request", "praise")',
    )

    @model_validator(mode="after")
    def _normalize_tags(self):
        if self.tags is not None:
            if len(self.tags) > 20:
                raise ValueError("tags cannot contain more than 20 entries")
            cleaned: List[str] = []
            for t in self.tags:
                if t is None:
                    continue
                token = t.strip().lower()
                if not token:
                    continue
                if len(token) > 64:
                    raise ValueError("each tag must be at most 64 characters")
                cleaned.append(token)
            self.tags = cleaned or None
        return self


# -------------------------------
# Create / Update payloads
# -------------------------------

class AppFeedbackCreate(AppFeedbackBase):
    """Payload required to create a new app-level feedback item."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "author_profile_id": "11111111-1111-1111-1111-111111111111",
                    "overall": 4,
                    "usability": 5,
                    "reliability": 4,
                    "performance": 4,
                    "support_experience": 5,
                    "headline": "Clean UX, a few hiccups",
                    "comment": "Great onboarding and messaging flow. Had one crash on the matches tab.",
                    "tags": ["praise", "bug"],
                },
                {
                    "overall": 5,
                    "headline": "Loving the new design",
                    "comment": "Everything feels faster now.",
                    "tags": ["praise"],
                },
            ]
        }
    }


class AppFeedbackUpdate(BaseModel):
    """Partial update (PATCH) for app-level feedback."""

    author_profile_id: Optional[UUID] = None

    overall: Optional[int] = Field(None, ge=1, le=5)
    usability: Optional[int] = Field(None, ge=1, le=5)
    reliability: Optional[int] = Field(None, ge=1, le=5)
    performance: Optional[int] = Field(None, ge=1, le=5)
    support_experience: Optional[int] = Field(None, ge=1, le=5)

    headline: Optional[str] = Field(None, min_length=1, max_length=120)
    comment: Optional[str] = Field(None, min_length=1, max_length=2000)
    tags: Optional[List[str]] = None

    @model_validator(mode="after")
    def _normalize_tags(self):
        if self.tags is not None:
            if len(self.tags) > 20:
                raise ValueError("tags cannot contain more than 20 entries")
            cleaned: List[str] = []
            for t in self.tags:
                if t is None:
                    continue
                token = t.strip().lower()
                if not token:
                    continue
                if len(token) > 64:
                    raise ValueError("each tag must be at most 64 characters")
                cleaned.append(token)
            self.tags = cleaned or None
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"overall": 5, "comment": "Upping my rating after latest bugfix release."},
                {"tags": ["feature-request", "dark-mode"]},
            ]
        }
    }


# -------------------------------
# Read model (id + timestamps)
# -------------------------------

class AppFeedbackOut(AppFeedbackBase):
    id: UUID = Field(default_factory=uuid4, description="Unique feedback identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp (UTC)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "created_at": "2025-10-02T12:00:00Z",
                    "updated_at": "2025-10-02T12:00:00Z",
                    "author_profile_id": "11111111-1111-1111-1111-111111111111",
                    "overall": 4,
                    "usability": 5,
                    "reliability": 4,
                    "performance": 4,
                    "support_experience": 5,
                    "headline": "Clean UX, a few hiccups",
                    "comment": "Great onboarding and messaging flow. Had one crash on the matches tab.",
                    "tags": ["praise", "bug"],
                }
            ]
        }
    }
