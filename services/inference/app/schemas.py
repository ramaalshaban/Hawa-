"""Request/response shapes. Field names mirror services/api/src/contracts.ts (camelCase)."""
from typing import Any, Literal

from pydantic import BaseModel, Field

SegmentKind = Literal["weather", "news", "banter"]
Host = Literal["anchor", "nightowl"]

# Ids become file names, so only allow safe characters (blocks "../" path tricks).
SAFE_ID = r"^[A-Za-z0-9_-]{1,100}$"


class FactSnapshot(BaseModel):
    id: str
    source: str
    takenAt: str
    data: dict[str, Any]


class ScriptRequest(BaseModel):
    kind: SegmentKind
    host: Host
    facts: list[FactSnapshot]


class ScriptResponse(BaseModel):
    text: str
    lang: str = "ar"
    source: Literal["llm", "fallback"]  # lets the worker/logs see when the template was used


class TtsRequest(BaseModel):
    id: str = Field(pattern=SAFE_ID)
    text: str = Field(min_length=1)
    voice: Host = "anchor"


class TtsResponse(BaseModel):
    path: str  # relative to data/, served by the API under /media
    durationS: float
