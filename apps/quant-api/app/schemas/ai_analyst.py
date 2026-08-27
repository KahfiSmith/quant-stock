from datetime import date, datetime

from pydantic import BaseModel, Field


class AiEvidence(BaseModel):
    category: str
    metric: str
    value: float | str | None
    source: str | None = None
    as_of: datetime | None = None
    period_end: date | None = None
    score_version: str | None = None


class AiAnalystResponse(BaseModel):
    symbol: str
    strengths: list[str]
    risks: list[str]
    unknowns: list[str]
    conclusion: str
    disclaimer: str
    # as_of: response wall-clock time (analysis generated at). NOT data freshness.
    as_of: datetime = Field(
        description="Wall-clock time when this analysis was generated. NOT data freshness.",
    )
    # analysis_engine: which engine produced this analysis.
    # "deterministic" = rule-based (no LLM call); "llm" = an actual LLM was used.
    analysis_engine: str = Field(
        description=(
            "Which engine produced this analysis: 'deterministic' (rule-based, no LLM call) "
            "or 'llm' (an LLM was called). Don't conflate with the legacy analysis_version label."
        ),
    )
    # provider: LLM provider used. None for deterministic engine.
    provider: str | None = Field(
        default=None,
        description="LLM provider identifier. None when analysis_engine='deterministic'.",
    )
    # model: LLM model identifier. None for deterministic engine.
    model: str | None = Field(
        default=None,
        description="LLM model identifier. None when analysis_engine='deterministic'.",
    )
    # analysis_version: kept for backward compat. New code should use analysis_engine/provider/model.
    analysis_version: str
    data_quality: str
    data_used: list[str] = Field(default_factory=list)
    data_unavailable: list[str] = Field(default_factory=list)
    evidence: list[AiEvidence] = Field(default_factory=list)
