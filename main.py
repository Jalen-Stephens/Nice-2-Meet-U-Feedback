from __future__ import annotations

import os
import socket
from datetime import datetime

from typing import Dict, List, Tuple
import base64
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi import Query, Path
from typing import Optional
from uuid import UUID


from models.health import Health
from models.profile_feedback import (
    ProfileFeedbackCreate,
    ProfileFeedbackOut,
    ProfileFeedbackUpdate,
)
from models.app_feedback import (
    AppFeedbackCreate,
    AppFeedbackOut,
    AppFeedbackUpdate,
)

port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------------------------
# Fake in-memory "databases"
# -----------------------------------------------------------------------------

app = FastAPI(title="Feedback Microservice", version="1.0.0")

# -----------------------------------------------------------------------------
# Health endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str]=None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
    )

@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    # Works because path_echo is optional in the model
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)


# -----------------------
# Simple cursor helpers
# -----------------------
def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()

def decode_cursor(cursor: Optional[str]) -> int:
    if not cursor:
        return 0
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cursor")

def paginate(items: List, limit: int, cursor: Optional[str]) -> Tuple[List, Optional[str]]:
    offset = decode_cursor(cursor)
    end = offset + limit
    page = items[offset:end]
    next_cursor = encode_cursor(end) if end < len(items) else None
    return page, next_cursor

# -----------------------
# In-memory stores
# -----------------------
_profile_feedback_store: Dict[UUID, ProfileFeedbackOut] = {}
_app_feedback_store: Dict[UUID, AppFeedbackOut] = {}

# ===================================================================
# PROFILE-TO-PROFILE FEEDBACK ROUTES
# Base: /feedback/profile
# ===================================================================

@app.post(
    "/feedback/profile",
    response_model=ProfileFeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
def create_profile_feedback(payload: ProfileFeedbackCreate):
    # Optional conflict: enforce one feedback per (match_id, reviewer) if match_id present
    if payload.match_id is not None:
        for item in _profile_feedback_store.values():
            if item.match_id == payload.match_id and item.reviewer_profile_id == payload.reviewer_profile_id:
                raise HTTPException(status_code=409, detail="Feedback already exists for this (match_id, reviewer)")

    now = datetime.utcnow()
    obj = ProfileFeedbackOut(
        id=uuid4(),
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    _profile_feedback_store[obj.id] = obj
    return obj

@app.get("/feedback/profile/{id}", response_model=ProfileFeedbackOut)
def get_profile_feedback(id: UUID = Path(...)):
    item = _profile_feedback_store.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@app.patch("/feedback/profile/{id}", response_model=ProfileFeedbackOut)
def update_profile_feedback(
    payload: ProfileFeedbackUpdate,
    id: UUID = Path(...),
):
    item = _profile_feedback_store.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    # If changing match_id/reviewer, re-check uniqueness
    new_match_id = payload.match_id if payload.match_id is not None else item.match_id
    new_reviewer = payload.reviewer_profile_id if payload.reviewer_profile_id is not None else item.reviewer_profile_id
    if new_match_id is not None:
        for other in _profile_feedback_store.values():
            if other.id == item.id:
                continue
            if other.match_id == new_match_id and other.reviewer_profile_id == new_reviewer:
                raise HTTPException(status_code=409, detail="Feedback already exists for this (match_id, reviewer)")

    data = item.model_dump()
    data.update(payload.model_dump(exclude_unset=True))
    data["updated_at"] = datetime.utcnow()
    updated = ProfileFeedbackOut(**data)
    _profile_feedback_store[id] = updated
    return updated

@app.delete("/feedback/profile/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile_feedback(id: UUID = Path(...)):
    if id not in _profile_feedback_store:
        raise HTTPException(status_code=404, detail="Not found")
    del _profile_feedback_store[id]
    return None

@app.get("/feedback/profile", response_model=Dict[str, object])
def list_profile_feedback(
    reviewee_profile_id: Optional[UUID] = Query(default=None),
    reviewer_profile_id: Optional[UUID] = Query(default=None),
    match_id: Optional[UUID] = Query(default=None),
    tags: Optional[str] = Query(default=None, description="Comma-separated list; OR semantics"),
    min_overall: Optional[int] = Query(default=None, ge=1, le=5),
    max_overall: Optional[int] = Query(default=None, ge=1, le=5),
    since: Optional[datetime] = Query(default=None),
    sort: str = Query(default="created_at", pattern="^(created_at|overall_experience)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
):
    items = list(_profile_feedback_store.values())

    if reviewee_profile_id:
        items = [i for i in items if i.reviewee_profile_id == reviewee_profile_id]
    if reviewer_profile_id:
        items = [i for i in items if i.reviewer_profile_id == reviewer_profile_id]
    if match_id:
        items = [i for i in items if i.match_id == match_id]
    if since:
        items = [i for i in items if i.created_at >= since]
    if min_overall is not None:
        items = [i for i in items if i.overall_experience >= min_overall]
    if max_overall is not None:
        items = [i for i in items if i.overall_experience <= max_overall]
    if tags:
        tag_set = {t.strip().lower() for t in tags.split(",") if t.strip()}
        if tag_set:
            items = [i for i in items if i.tags and (set(i.tags) & tag_set)]

    reverse = order == "desc"
    if sort == "created_at":
        items.sort(key=lambda i: (i.created_at, i.id.hex), reverse=reverse)
    else:  # overall_experience
        items.sort(key=lambda i: (i.overall_experience, i.created_at, i.id.hex), reverse=reverse)

    page, next_cursor = paginate(items, limit, cursor)
    return {"items": page, "next_cursor": next_cursor, "count": len(page)}

@app.get("/feedback/profile/stats", response_model=Dict[str, object])
def profile_feedback_stats(
    reviewee_profile_id: UUID = Query(...),
    tags: Optional[str] = Query(default=None),
    since: Optional[datetime] = Query(default=None),
):
    items = [i for i in _profile_feedback_store.values() if i.reviewee_profile_id == reviewee_profile_id]
    if since:
        items = [i for i in items if i.created_at >= since]
    if tags:
        tag_set = {t.strip().lower() for t in tags.split(",") if t.strip()}
        if tag_set:
            items = [i for i in items if i.tags and (set(i.tags) & tag_set)]

    total = len(items)
    if total == 0:
        return {
            "reviewee_profile_id": reviewee_profile_id,
            "count_total": 0,
            "avg_overall_experience": None,
            "distribution_overall_experience": {str(k): 0 for k in range(1, 6)},
            "facet_averages": {"safety_feeling": None, "respectfulness": None},
            "top_tags": [],
        }

    def avg(nums: List[int]) -> float:
        return round(sum(nums) / len(nums), 3) if nums else None

    overall_vals = [i.overall_experience for i in items]
    dist = {str(k): 0 for k in range(1, 6)}
    for v in overall_vals:
        dist[str(v)] += 1

    safety_vals = [i.safety_feeling for i in items if i.safety_feeling is not None]
    respect_vals = [i.respectfulness for i in items if i.respectfulness is not None]

    tag_counts: Dict[str, int] = {}
    for i in items:
        if i.tags:
            for t in i.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]

    return {
        "reviewee_profile_id": reviewee_profile_id,
        "count_total": total,
        "avg_overall_experience": avg(overall_vals),
        "distribution_overall_experience": dist,
        "facet_averages": {
            "safety_feeling": avg(safety_vals),
            "respectfulness": avg(respect_vals),
        },
        "top_tags": [{"tag": k, "count": v} for k, v in top_tags],
    }

# ===================================================================
# APP-LEVEL FEEDBACK ROUTES
# Base: /feedback/app
# ===================================================================

@app.post(
    "/feedback/app",
    response_model=AppFeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
def create_app_feedback(payload: AppFeedbackCreate):
    now = datetime.utcnow()
    obj = AppFeedbackOut(
        id=uuid4(),
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    _app_feedback_store[obj.id] = obj
    return obj

@app.get("/feedback/app/{id}", response_model=AppFeedbackOut)
def get_app_feedback(id: UUID = Path(...)):
    item = _app_feedback_store.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@app.patch("/feedback/app/{id}", response_model=AppFeedbackOut)
def update_app_feedback(
    payload: AppFeedbackUpdate,
    id: UUID = Path(...),
):
    item = _app_feedback_store.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    data = item.model_dump()
    data.update(payload.model_dump(exclude_unset=True))
    data["updated_at"] = datetime.utcnow()
    updated = AppFeedbackOut(**data)
    _app_feedback_store[id] = updated
    return updated

@app.delete("/feedback/app/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app_feedback(id: UUID = Path(...)):
    if id not in _app_feedback_store:
        raise HTTPException(status_code=404, detail="Not found")
    del _app_feedback_store[id]
    return None

@app.get("/feedback/app", response_model=Dict[str, object])
def list_app_feedback(
    author_profile_id: Optional[UUID] = Query(default=None),
    tags: Optional[str] = Query(default=None, description="Comma-separated list; OR semantics"),
    min_overall: Optional[int] = Query(default=None, ge=1, le=5),
    max_overall: Optional[int] = Query(default=None, ge=1, le=5),
    since: Optional[datetime] = Query(default=None),
    sort: str = Query(default="created_at", pattern="^(created_at|overall)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
):
    items = list(_app_feedback_store.values())

    if author_profile_id:
        items = [i for i in items if i.author_profile_id == author_profile_id]
    if since:
        items = [i for i in items if i.created_at >= since]
    if min_overall is not None:
        items = [i for i in items if i.overall >= min_overall]
    if max_overall is not None:
        items = [i for i in items if i.overall <= max_overall]
    if tags:
        tag_set = {t.strip().lower() for t in tags.split(",") if t.strip()}
        if tag_set:
            items = [i for i in items if i.tags and (set(i.tags) & tag_set)]

    reverse = order == "desc"
    if sort == "created_at":
        items.sort(key=lambda i: (i.created_at, i.id.hex), reverse=reverse)
    else:  # overall
        items.sort(key=lambda i: (i.overall, i.created_at, i.id.hex), reverse=reverse)

    page, next_cursor = paginate(items, limit, cursor)
    return {"items": page, "next_cursor": next_cursor, "count": len(page)}

@app.get("/feedback/app/stats", response_model=Dict[str, object])
def app_feedback_stats(
    tags: Optional[str] = Query(default=None),
    since: Optional[datetime] = Query(default=None),
):
    items = list(_app_feedback_store.values())
    if since:
        items = [i for i in items if i.created_at >= since]
    if tags:
        tag_set = {t.strip().lower() for t in tags.split(",") if t.strip()}
        if tag_set:
            items = [i for i in items if i.tags and (set(i.tags) & tag_set)]

    total = len(items)
    if total == 0:
        return {
            "count_total": 0,
            "avg_overall": None,
            "distribution_overall": {str(k): 0 for k in range(1, 6)},
            "facet_averages": {"usability": None, "reliability": None, "performance": None, "support_experience": None},
            "top_tags": [],
        }

    def avg(nums: List[int]) -> float:
        return round(sum(nums) / len(nums), 3) if nums else None

    overall_vals = [i.overall for i in items]
    dist = {str(k): 0 for k in range(1, 6)}
    for v in overall_vals:
        dist[str(v)] += 1

    usability_vals = [i.usability for i in items if i.usability is not None]
    reliability_vals = [i.reliability for i in items if i.reliability is not None]
    performance_vals = [i.performance for i in items if i.performance is not None]
    support_vals = [i.support_experience for i in items if i.support_experience is not None]

    tag_counts: Dict[str, int] = {}
    for i in items:
        if i.tags:
            for t in i.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]

    return {
        "count_total": total,
        "avg_overall": avg(overall_vals),
        "distribution_overall": dist,
        "facet_averages": {
            "usability": avg(usability_vals),
            "reliability": avg(reliability_vals),
            "performance": avg(performance_vals),
            "support_experience": avg(support_vals),
        },
        "top_tags": [{"tag": k, "count": v} for k, v in top_tags],
    }

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
