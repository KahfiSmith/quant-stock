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
    TECHNICAL: (symbol: string) => ["market", "technical", symbol] as const,
    FUNDAMENTAL: (symbol: string) => ["market", "fundamental", symbol] as const,
    SCORE: (symbol: string) => ["market", "score", symbol] as const,
    SCREENER: (filters: Record<string, unknown>) => ["market", "screener", filters] as const,
  },
} as const;
