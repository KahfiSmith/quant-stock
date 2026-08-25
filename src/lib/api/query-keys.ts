export const QUERY_KEYS = {
  AUTH: {
    SESSION: ["auth", "session"] as const,
  },
  USER: {
    PROFILE: ["user", "profile"] as const,
  },
  MARKET: {
    STOCKS: ["market", "stocks"] as const,
    PRICES: (symbol: string) => ["market", "prices", symbol] as const,
  },
} as const;
