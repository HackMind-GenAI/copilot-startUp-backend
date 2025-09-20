
from __future__ import annotations

from typing import List
from pydantic import BaseModel

class FounderSummaryRequest(BaseModel):
    founder: str

class FounderSummaryResponse(BaseModel):
    name: str
    workedWithInPast: List[str]
    risk: str
    pastVentureResult: str
    communicationStyle: str
    resilienceAndGrit: str
    salesOrProductOriented: str
