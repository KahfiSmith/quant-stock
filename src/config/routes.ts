export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  PROFILE: "/profile",
  SETTINGS: "/settings",
  STOCKS: "/stocks",
  PORTFOLIO: "/portfolio",
  BACKTEST: "/backtest",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];
