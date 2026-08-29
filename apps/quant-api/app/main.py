from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.errors import ApiError, api_error_handler, validation_error_handler
from app.api.routes import auth, backtest, health, idx_routes, market_data, portfolio, screener
from app.core.config import Settings, get_settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.db.session import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    app = FastAPI(title="QuantLens API", version="0.1.0")
    app.state.settings = active_settings
    app.state.database = Database(active_settings)
    app.state.auth_rate_limiter = SlidingWindowRateLimiter(active_settings.auth_rate_limit_per_minute)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def limit_auth_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "POST" and request.url.path.startswith("/api/v1/auth/"):
            client_host = request.client.host if request.client else "unknown"
            if not app.state.auth_rate_limiter.allow(client_host):
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "message": "Too many authentication requests",
                        "code": "RATE_LIMITED",
                        "error": None,
                    },
                )
        return await call_next(request)

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(market_data.router)
    app.include_router(screener.router)
    app.include_router(portfolio.router)
    app.include_router(backtest.router)
    app.include_router(idx_routes.router)
    return app


app = create_app()
