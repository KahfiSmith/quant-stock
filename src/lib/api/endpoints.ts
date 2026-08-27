export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: "/api/v1/auth/login",
    LOGOUT: "/api/v1/auth/logout",
    REFRESH: "/api/v1/auth/refresh",
    REGISTER: "/api/v1/auth/register",
    DELETE_ACCOUNT: "/api/v1/auth/account",
    ME: "/api/v1/auth/me",
  },
  BACKTEST: {
    RUN: "/api/v1/backtest",
  },
  PORTFOLIO: {
    LIST: "/api/v1/portfolios",
    CREATE: "/api/v1/portfolios",
    DETAIL: (id: number | string) => `/api/v1/portfolios/${id}`,
    ADD_TRANSACTION: (id: number | string) => `/api/v1/portfolios/${id}/transactions`,
  },
  MARKET: {
    STOCKS: "/api/v1/stocks",
    PRICES: (symbol: string) => `/api/v1/stocks/${symbol}/prices`,
    TECHNICAL: (symbol: string) => `/api/v1/stocks/${symbol}/technical`,
    FUNDAMENTAL: (symbol: string) => `/api/v1/stocks/${symbol}/fundamental`,
    SCORE: (symbol: string) => `/api/v1/stocks/${symbol}/score`,
    AI_SUMMARY: (symbol: string) => `/api/v1/stocks/${symbol}/ai-summary`,
    SCREENER: "/api/v1/screener",
  },
} as const;
