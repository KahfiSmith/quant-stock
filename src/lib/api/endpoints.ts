export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: "/api/v1/auth/login",
    LOGOUT: "/api/v1/auth/logout",
    REFRESH: "/api/v1/auth/refresh",
    REGISTER: "/api/v1/auth/register",
    DELETE_ACCOUNT: "/api/v1/auth/account",
    ME: "/api/v1/auth/me",
  },
} as const;
