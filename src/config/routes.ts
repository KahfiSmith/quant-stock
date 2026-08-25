export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  PROFILE: "/profile",
  STOCKS: "/stocks",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];
