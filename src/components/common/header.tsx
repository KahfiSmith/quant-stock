"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ROUTES } from "@/config/routes";
import { siteConfig } from "@/config/site";
import { useAuthStore } from "@/store";

export function Header() {
  const user = useAuthStore((state) => state.user);
  const pathname = usePathname();

  const getLinkClasses = (href: string) => {
    const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));
    return isActive
      ? "font-bold text-primary underline underline-offset-4 transition-colors"
      : "hover:text-foreground transition-colors";
  };

  return (
    <header className="border-b bg-background/80 backdrop-blur sticky top-0 z-50">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
        <Link className="text-lg font-bold tracking-tight text-primary flex items-center gap-2" href={ROUTES.HOME}>
          <span className="bg-primary text-primary-foreground text-xs px-2 py-0.5 rounded font-mono">Q</span>
          {siteConfig.name}
        </Link>

        <nav className="flex items-center gap-5 text-sm font-medium text-muted-foreground">
          <Link className={getLinkClasses(ROUTES.HOME)} href={ROUTES.HOME}>
            Home
          </Link>
          <Link className={getLinkClasses(ROUTES.QUANT_RANKING)} href={ROUTES.QUANT_RANKING}>
            Quant Ranking
          </Link>
          <Link className={getLinkClasses(ROUTES.STOCKS)} href={ROUTES.STOCKS}>
            Stocks
          </Link>
          <Link className={getLinkClasses(ROUTES.PORTFOLIO)} href={ROUTES.PORTFOLIO}>
            Portfolio
          </Link>
          <Link className={getLinkClasses(ROUTES.BACKTEST)} href={ROUTES.BACKTEST}>
            IDX Factor Rotation
          </Link>

          {user ? (
            <div className="flex items-center gap-3 pl-3 border-l">
              <Link className={getLinkClasses(ROUTES.PROFILE)} href={ROUTES.PROFILE}>
                Profile
              </Link>
              <Link className={getLinkClasses(ROUTES.SETTINGS)} href={ROUTES.SETTINGS}>
                Settings
              </Link>
            </div>
          ) : (
            <div className="flex items-center gap-3 pl-3 border-l">
              <Link className={getLinkClasses(ROUTES.LOGIN)} href={ROUTES.LOGIN}>
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
