from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.errors import ApiError, success
from app.models.backtest import BacktestJob
from app.models.user import User
from app.quant.backtest import run_strategy_backtest
from app.schemas.backtest import BacktestJobItem, BacktestJobListResponse, BacktestRequest, BacktestResponse

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


@router.post("", response_model=None)
def post_backtest(
    body: BacktestRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    result: BacktestResponse = run_strategy_backtest(db, body, user=user)
    return success(result.model_dump(mode="json"), "Backtest completed successfully")


@router.get("/jobs", response_model=None)
def list_backtest_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    jobs = list(
        db.scalars(
            select(BacktestJob)
            .where(BacktestJob.user_id == user.id)
            .order_by(BacktestJob.created_at.desc())
        )
    )
    items = [
        BacktestJobItem(
            id=job.id,
            symbol=job.symbol,
            strategy=job.strategy,
            status=job.status,  # type: ignore[arg-type]
            initial_capital=job.initial_capital,
            parameters=job.parameters,
            start_date=job.start_date,
            end_date=job.end_date,
            summary=job.summary,  # type: ignore[arg-type]
            equity_curve=job.equity_curve,  # type: ignore[arg-type]
            metadata=job.metadata_json,
            error_message=job.error_message,
            retry_count=job.retry_count,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
        for job in jobs
    ]
    resp = BacktestJobListResponse(items=items, total=len(items))
    return success(resp.model_dump(mode="json"), "Backtest jobs retrieved successfully")


@router.get("/jobs/{job_id}", response_model=None)
def get_backtest_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    job = db.scalar(
        select(BacktestJob).where(BacktestJob.id == job_id, BacktestJob.user_id == user.id)
    )
    if not job:
        raise ApiError(404, "JOB_NOT_FOUND", f"Backtest job not found: {job_id}")

    item = BacktestJobItem(
        id=job.id,
        symbol=job.symbol,
        strategy=job.strategy,
        status=job.status,  # type: ignore[arg-type]
        initial_capital=job.initial_capital,
        parameters=job.parameters,
        start_date=job.start_date,
        end_date=job.end_date,
        summary=job.summary,  # type: ignore[arg-type]
        equity_curve=job.equity_curve,  # type: ignore[arg-type]
        metadata=job.metadata_json,
        error_message=job.error_message,
        retry_count=job.retry_count,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
    return success(item.model_dump(mode="json"), "Backtest job retrieved successfully")
