# Authentication API and Errors

The active QuantLens backend is the FastAPI service in `apps/quant-api`, normally available at `http://localhost:8000`. Authentication calls use `authClient` with credentials; protected calls use `apiClient` with an in-memory Bearer access token.

## Implemented endpoints

| Method | Path | Purpose | Frontend integration |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Create a numeric-ID user account | `RegisterForm` → `useRegister` |
| `POST` | `/api/v1/auth/login` | Issue access token and HttpOnly refresh cookie | `LoginForm` → `useLogin` |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token and issue access token | session bootstrap and single-flight retry |
| `POST` | `/api/v1/auth/logout` | Revoke refresh-session family and clear cookie | `LogoutButton` → `useLogout` |
| `GET` | `/api/v1/auth/me` | Return the authenticated user and preferences | available for profile queries |
| `PATCH` | `/api/v1/auth/me` | Update name, theme preference, and timezone | `/settings` → `useUpdateProfile` |
| `DELETE` | `/api/v1/auth/account` | Confirm password and delete the current account | `DeleteAccountButton` → `useDeleteAccount` |

Google OAuth, password reset, and email verification are deliberately deferred and are not active FastAPI endpoints.

## Contract

Successful responses use `{ "success": true, "message": "...", "data": {} }`. Failed responses use `{ "success": false, "message": "...", "code": "ERROR_CODE", "error": null }`.

Login and refresh return:

```json
{
  "access_token": "jwt",
  "expires_in": 900,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Quant User",
    "theme_preference": "system",
    "timezone": "UTC",
    "role": "user",
    "is_email_verified": false
  }
}
```

`id` is a numeric, auto-incrementing user ID. Profile responses also include `theme_preference` (`light`, `dark`, or `system`) and `timezone`. The refresh credential is opaque, HMAC-hashed before persistence, is never exposed in JSON, and is sent only in an HttpOnly cookie.

`PATCH /api/v1/auth/me` accepts `name`, `theme_preference`, and `timezone`; omitted fields remain unchanged.

## Relevant error codes

- `INVALID_CREDENTIALS`, `EMAIL_ALREADY_REGISTERED`, `ACCOUNT_DISABLED`
- `ACCESS_TOKEN_MISSING`, `ACCESS_TOKEN_INVALID`, `ACCESS_TOKEN_EXPIRED`
- `REFRESH_TOKEN_MISSING`, `REFRESH_TOKEN_INVALID`, `REFRESH_TOKEN_EXPIRED`, `REFRESH_TOKEN_REUSED`, `SESSION_REVOKED`
- `FORBIDDEN`, `VALIDATION_ERROR`, `RATE_LIMITED`
