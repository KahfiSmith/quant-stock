from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fundamental.scoring import calculate_fundamental_score
from app.models.fundamental import Fundamental
from app.models.market_data import Stock
from app.schemas.fundamental import FundamentalResponse, RatiosSummary


def get_latest_fundamental(db: Session, stock: Stock) -> FundamentalResponse | None:
    record = db.scalar(
        select(Fundamental)
        .where(Fundamental.stock_id == stock.id)
        .order_by(Fundamental.period_end.desc())
        .limit(1)
    )

    if record is None:
        return None

    pe = float(record.pe_ratio) if record.pe_ratio is not None else None
    pb = float(record.pb_ratio) if record.pb_ratio is not None else None
    roe = float(record.roe) if record.roe is not None else None
    roa = float(record.roa) if record.roa is not None else None
    de = float(record.debt_to_equity) if record.debt_to_equity is not None else None
    rev_g = float(record.revenue_growth) if record.revenue_growth is not None else None
    eps_g = float(record.eps_growth) if record.eps_growth is not None else None

    calculated_score = float(record.score) if record.score is not None else calculate_fundamental_score(
        pe, pb, roe, roa, de, rev_g, eps_g
    )

    return FundamentalResponse(
        symbol=stock.symbol,
        period_end=record.period_end,
        published_at=record.published_at,
        period_type=record.period_type,
        score=calculated_score,
        ratios=RatiosSummary(
            pe_ratio=pe,
            pb_ratio=pb,
            roe=roe,
            roa=roa,
            debt_to_equity=de,
            revenue_growth=rev_g,
            eps_growth=eps_g,
        ),
        source=record.source,
        as_of=datetime.now(UTC),
    )
