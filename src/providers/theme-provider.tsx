"use client";

import { useEffect } from "react";

import { useThemeStore } from "@/store";

/**
 * Keeps the DOM theme class in sync with the Zustand store after ThemeScript
 * has already prevented the initial flash. Also listens for OS-level
 * color-scheme changes when the user selects "system".
 */
export function ThemeProvider({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const theme = useThemeStore((s) => s.theme);

  useEffect(() => {
    if (theme !== "system") return;

    const mql = window.matchMedia("(prefers-color-scheme: dark)");

    function handleChange(e: MediaQueryListEvent) {
      const resolved = e.matches ? "dark" : "light";
      const root = document.documentElement;
      root.classList.remove("light", "dark");
      root.classList.add(resolved);
      root.style.colorScheme = resolved;
    }

    mql.addEventListener("change", handleChange);
    return () => mql.removeEventListener("change", handleChange);
  }, [theme]);

  useEffect(() => {
    const root = document.documentElement;
    let resolved = theme;
    if (theme === "system") {
      resolved = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    }
    root.classList.remove("light", "dark");
    root.classList.add(resolved);
    root.style.colorScheme = resolved;
  }, [theme]);

  return <>{children}</>;
}
