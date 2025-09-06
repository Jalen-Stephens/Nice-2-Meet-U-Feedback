from pydantic import BaseModel, Field
from typing import Optional

class Health(BaseModel):
    status: int = Field(description="Numeric status code (e.g., 200 for OK)")
    status_message: str = Field(description="Human-readable status message")
    timestamp: str = Field(description="Timestamp in ISO 8601 format (UTC)")
    ip_address: str = Field(description="IP address of the responding service")
    echo: str | None = Field(default=None, description="Optional echo (query param)")
    path_echo: str | None = Field(default=None, description="Echo from path param (/health/{path_echo})")

    # Pydantic v2 style
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": 200,
                "status_message": "OK",
                "timestamp": "2025-09-02T12:34:56Z",
                "ip_address": "192.168.1.10",
                "echo": "Hello from query",
                "path_echo": "Hello from path"
            }
        }
    }