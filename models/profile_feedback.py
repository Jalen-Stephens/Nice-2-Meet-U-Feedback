# profile_feedback.py
"""
Schemas for profile-to-profile feedback in the Feedback microservice.

This module defines layered Pydantic models:
- ProfileFeedbackBase: shared domain fields (no id/timestamps)
- ProfileFeedbackCreate: payload required to create feedback
- ProfileFeedbackUpdate: partial update (PATCH)
- ProfileFeedbackOut: read model including id and timestamps

Notes:
- No moderation/privacy/context fields per product spec.
- Supports optional `match_id` for dedupe/linking to a specific match.
- Validates rating ranges and that reviewer != reviewee when both provided.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


# -------------------------------
# Shared domain (no ids/dates)
# -------------------------------

class ProfileFeedbackBase(BaseModel):
    reviewer_profile_id: UUID = Field(..., description="Profile leaving the feedback")
    reviewee_profile_id: UUID = Field(..., description="Profile receiving the feedback")
    match_id: Optional[UUID] = Field(
        None,
        description="Optional link to the specific match this feedback pertains to",
    )

    # Ratings / outcomes
    overall_experience: int = Field(
        ...,
        ge=1,
        le=5,
        description="Required overall rating from 1 (worst) to 5 (best)",
    )
    would_meet_again: Optional[bool] = Field(
        None, description="Whether the reviewer would meet the reviewee again"
    )
    safety_feeling: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Optional perceived safety rating from 1 to 5",
    )
    respectfulness: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Optional respectfulness rating from 1 to 5",
    )

    # Qualitative
    headline: Optional[str] = Field(
        None,
        min_length=1,
        max_length=120,
        description="Optional short title summarizing the feedback",
    )
    comment: Optional[str] = Field(
        None,
        min_length=1,
        max_length=2000,
        description="Optional free-text comment; max 2000 characters",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description='Optional list of simple tags (e.g., "great-convo", "no-show")',
    )

    @model_validator(mode="after")
    def _normalize_and_check(self):
        # reviewer != reviewee (when both present)
        if (
            getattr(self, "reviewer_profile_id", None) is not None
            and getattr(self, "reviewee_profile_id", None) is not None
            and self.reviewer_profile_id == self.reviewee_profile_id
        ):
            raise ValueError("reviewer_profile_id must not equal reviewee_profile_id")

        # normalize tags if present
        if self.tags is not None:
            # strip/normalize; enforce simple, non-empty tokens; limit list length
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

class ProfileFeedbackCreate(ProfileFeedbackBase):
    """Payload required to create a new profile-to-profile feedback item."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reviewer_profile_id": "11111111-1111-1111-1111-111111111111",
                    "reviewee_profile_id": "22222222-2222-2222-2222-222222222222",
                    "match_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "overall_experience": 5,
                    "would_meet_again": True,
                    "safety_feeling": 5,
                    "respectfulness": 5,
                    "headline": "Great first coffee",
                    "comment": "Easy conversation, very respectful and punctual.",
                    "tags": ["great-convo", "punctual"],
                }
            ]
        }
    }


class ProfileFeedbackUpdate(BaseModel):
    """Partial update (PATCH) for profile-to-profile feedback."""

    reviewer_profile_id: Optional[UUID] = None
    reviewee_profile_id: Optional[UUID] = None
    match_id: Optional[UUID] = None

    overall_experience: Optional[int] = Field(None, ge=1, le=5)
    would_meet_again: Optional[bool] = None
    safety_feeling: Optional[int] = Field(None, ge=1, le=5)
    respectfulness: Optional[int] = Field(None, ge=1, le=5)

    headline: Optional[str] = Field(None, min_length=1, max_length=120)
    comment: Optional[str] = Field(None, min_length=1, max_length=2000)
    tags: Optional[List[str]] = None

    @model_validator(mode="after")
    def _validate_ids_and_tags(self):
        # Only check inequality if both IDs supplied in the same patch
        if (
            self.reviewer_profile_id is not None
            and self.reviewee_profile_id is not None
            and self.reviewer_profile_id == self.reviewee_profile_id
        ):
            raise ValueError("reviewer_profile_id must not equal reviewee_profile_id")

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
                {"overall_experience": 4, "comment": "Updating after a second meetup."},
                {"tags": ["follow-up", "still-positive"]},
            ]
        }
    }


# -------------------------------
# Read model (id + timestamps)
# -------------------------------

class ProfileFeedbackOut(ProfileFeedbackBase):
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
                    "id": "33333333-3333-3333-3333-333333333333",
                    "created_at": "2025-10-02T12:00:00Z",
                    "updated_at": "2025-10-02T12:00:00Z",
                    "reviewer_profile_id": "11111111-1111-1111-1111-111111111111",
                    "reviewee_profile_id": "22222222-2222-2222-2222-222222222222",
                    "match_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "overall_experience": 5,
                    "would_meet_again": True,
                    "safety_feeling": 5,
                    "respectfulness": 5,
                    "headline": "Great first coffee",
                    "comment": "Easy conversation, very respectful and punctual.",
                    "tags": ["great-convo", "punctual"],
                }
            ]
        }
    }
