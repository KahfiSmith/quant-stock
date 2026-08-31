"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { ROUTES } from "@/config/routes";
import { siteConfig } from "@/config/site";
import { useAuthStore } from "@/store";

const NAV_LINKS = [
  { href: ROUTES.HOME, label: "Home" },
  { href: ROUTES.QUANT_RANKING, label: "Quant Ranking" },
  { href: ROUTES.SCANNER, label: "Scanner" },
  { href: ROUTES.STOCKS, label: "Stocks" },
  { href: ROUTES.PORTFOLIO, label: "Portfolio" },
  { href: ROUTES.BACKTEST, label: "IDX Factor Rotation" },
];

export function Header() {
  const user = useAuthStore((state) => state.user);
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const getLinkClasses = (href: string) => {
    const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));
    return isActive
      ? "font-bold text-primary underline underline-offset-4 transition-colors"
      : "hover:text-foreground transition-colors";
  };

  const closeMobile = () => setMobileOpen(false);

  return (
    <header className="border-b bg-background/80 backdrop-blur sticky top-0 z-50">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
        <Link className="text-lg font-bold tracking-tight text-primary flex items-center gap-2" href={ROUTES.HOME}>
          <span className="bg-primary text-primary-foreground text-xs px-2 py-0.5 rounded font-mono">Q</span>
          {siteConfig.name}
        </Link>

        <nav className="hidden items-center gap-5 text-sm font-medium text-muted-foreground md:flex">
          {NAV_LINKS.map((link) => (
            <Link key={link.href} className={getLinkClasses(link.href)} href={link.href}>
              {link.label}
            </Link>
          ))}

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

        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 text-muted-foreground hover:text-foreground"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileOpen && (
        <nav className="border-t bg-background px-6 py-4 md:hidden">
          <div className="flex flex-col gap-3 text-sm font-medium text-muted-foreground">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                className={`py-1 ${getLinkClasses(link.href)}`}
                href={link.href}
                onClick={closeMobile}
              >
                {link.label}
              </Link>
            ))}
            <div className="border-t pt-3 mt-1 flex flex-col gap-3">
              {user ? (
                <>
                  <Link className={`py-1 ${getLinkClasses(ROUTES.PROFILE)}`} href={ROUTES.PROFILE} onClick={closeMobile}>
                    Profile
                  </Link>
                  <Link className={`py-1 ${getLinkClasses(ROUTES.SETTINGS)}`} href={ROUTES.SETTINGS} onClick={closeMobile}>
                    Settings
                  </Link>
                </>
              ) : (
                <>
                  <Link className={`py-1 ${getLinkClasses(ROUTES.LOGIN)}`} href={ROUTES.LOGIN} onClick={closeMobile}>
                    Login
                  </Link>
                  <Link
                    className="w-fit rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground"
                    href={ROUTES.REGISTER}
                    onClick={closeMobile}
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}
