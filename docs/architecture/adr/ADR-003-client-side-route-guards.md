# ADR-003: Client-Side Route Guards over Middleware

## Context

Protected pages (`/profile`) must redirect unauthenticated users to `/login`,
and `/login` must redirect authenticated users away. Options:

- Next.js `middleware.ts` — runs before render, can redirect server-side.
- Client-side guards in the page components — read `useAuthStore` status and
  redirect with `router.replace`.

At the time of this decision the session lives in client memory and is only
restored asynchronously (`SessionProvider` bootstraps on mount), so a
middleware check cannot know the auth state without its own server-side
session source.

## Decision

- `middleware.ts` is a pass-through (`NextResponse.next()`) and does not
  enforce access control.
- Protection is delegated to shared guard components in
  `src/components/features/auth/route-guards.tsx`:
  - `RequireAuth` redirects unauthenticated users to `/login`.
  - `RedirectAuthenticated` redirects authenticated users to `/profile`.
- Guards read `useAuthStore` status and render a loading state while the
  session is `checking`/`idle`.

## Consequences

- No server-side enforcement exists; the backend remains the real security
  boundary (protected routes reject without a valid Bearer token).
- Guard logic is centralized in shared `RequireAuth`/`RedirectAuthenticated`
  components, so protected pages opt in by wrapping their content rather than
  duplicating redirect logic.
- Redirects happen after hydration, so there is a brief flash while the
  session boots.

## Status

Accepted.
