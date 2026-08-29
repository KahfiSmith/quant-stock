"use client";

import Link from "next/link";

import { ROUTES } from "@/config/routes";
import { siteConfig } from "@/config/site";
import { useAuthStore } from "@/store";

export function Header() {
  const user = useAuthStore((state) => state.user);

  return (
    <header className="border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
        <Link className="font-semibold tracking-tight text-primary" href={ROUTES.HOME}>
          {siteConfig.name}
        </Link>

        <nav className="flex items-center gap-5 text-sm font-medium text-muted-foreground">
          <Link className="hover:text-foreground transition-colors" href={ROUTES.HOME}>
            Home
          </Link>
          <Link className="hover:text-foreground transition-colors" href={ROUTES.STOCKS}>
            Stocks
          </Link>
          <Link className="hover:text-foreground transition-colors" href={ROUTES.PORTFOLIO}>
            Portfolio
          </Link>
          <Link className="hover:text-foreground transition-colors" href={ROUTES.BACKTEST}>
            Backtest
          </Link>

          {user ? (
            <div className="flex items-center gap-3 pl-3 border-l">
              <Link className="hover:text-foreground transition-colors" href={ROUTES.PROFILE}>
                Profile
              </Link>
              <Link className="hover:text-foreground transition-colors" href={ROUTES.SETTINGS}>
                Settings
              </Link>
            </div>
          ) : (
            <div className="flex items-center gap-3 pl-3 border-l">
              <Link className="hover:text-foreground transition-colors" href={ROUTES.LOGIN}>
                Login
              </Link>
              <Link
                className="rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
                href={ROUTES.REGISTER}
              >
                Register
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
