"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";

import { Loading } from "@/components/common";
import { ROUTES } from "@/config/routes";
import { useAuthStore } from "@/store";
import type { AuthStatus } from "@/store/auth-store";

type RouteGuardProps = {
  children: ReactNode;
};

const SESSION_DECIDING: AuthStatus[] = ["idle", "checking"];

function useSessionStatus() {
  const router = useRouter();
  const status = useAuthStore((state) => state.status);
  return { router, status };
}

function SessionLoading() {
  return <Loading />;
}


export function RequireAuth({ children }: RouteGuardProps) {
  const { router, status } = useSessionStatus();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.replace(ROUTES.LOGIN);
    }
  }, [router, status]);

  if (status !== "authenticated") {
    return <SessionLoading />;
  }

  return <>{children}</>;
}


export function RedirectAuthenticated({ children }: RouteGuardProps) {
  const { router, status } = useSessionStatus();

  useEffect(() => {
    if (status === "authenticated") {
      router.replace(ROUTES.PROFILE);
    }
  }, [router, status]);

  if (SESSION_DECIDING.includes(status) || status === "authenticated") {
    return <SessionLoading />;
  }

  return <>{children}</>;
}