import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RedirectAuthenticated, RequireAuth } from "@/components/features/auth/route-guards";
import { ROUTES } from "@/config/routes";
import { useAuthStore } from "@/store";

const mocks = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push, replace: mocks.replace }),
}));

const user = {
  id: 1,
  email: "user@example.com",
  name: "Quant User",
  role: "user",
  is_email_verified: false,
};

function setStatus(status: "idle" | "checking" | "unauthenticated") {
  useAuthStore.setState({ status, accessToken: null, user: null });
}

function setAuthenticated() {
  useAuthStore.setState({ status: "authenticated", accessToken: "access-123", user });
}

beforeEach(() => {
  mocks.replace.mockReset();
});

describe("RequireAuth", () => {
  it("renders children for an authenticated user", () => {
    setAuthenticated();
    render(
      <RequireAuth>
        <p>secret content</p>
      </RequireAuth>
    );
    expect(screen.getByText("secret content")).toBeInTheDocument();
    expect(mocks.replace).not.toHaveBeenCalled();
  });

  it("redirects unauthenticated users to login without rendering children", () => {
    setStatus("unauthenticated");
    render(
      <RequireAuth>
        <p>secret content</p>
      </RequireAuth>
    );
    expect(mocks.replace).toHaveBeenCalledWith(ROUTES.LOGIN);
    expect(screen.queryByText("secret content")).not.toBeInTheDocument();
  });

  it("shows a loading state while the session is being resolved", () => {
    setStatus("checking");
    const { container } = render(
      <RequireAuth>
        <p>secret content</p>
      </RequireAuth>
    );
    expect(screen.queryByText("secret content")).not.toBeInTheDocument();
    expect(container.querySelector("svg")).not.toBeNull();
  });
});

describe("RedirectAuthenticated", () => {
  it("renders children for an unauthenticated user", () => {
    setStatus("unauthenticated");
    render(
      <RedirectAuthenticated>
        <p>login form</p>
      </RedirectAuthenticated>
    );
    expect(screen.getByText("login form")).toBeInTheDocument();
  });

  it("redirects authenticated users to the profile without rendering children", () => {
    setAuthenticated();
    render(
      <RedirectAuthenticated>
        <p>login form</p>
      </RedirectAuthenticated>
    );
    expect(mocks.replace).toHaveBeenCalledWith(ROUTES.PROFILE);
    expect(screen.queryByText("login form")).not.toBeInTheDocument();
  });
});