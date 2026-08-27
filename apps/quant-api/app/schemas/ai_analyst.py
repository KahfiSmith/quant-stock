from datetime import datetime

from pydantic import BaseModel


class AiAnalystResponse(BaseModel):
    symbol: str
    strengths: list[str]
    risks: list[str]
    unknowns: list[str]
    conclusion: str
    disclaimer: str
    as_of: datetime
