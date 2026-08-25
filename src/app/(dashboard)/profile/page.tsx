"use client";

import Link from "next/link";

import { DeleteAccountButton, LogoutButton, RequireAuth } from "@/components/features/auth";
import { Button } from "@/components/ui/button";
import { ROUTES } from "@/config/routes";
import { useAuthStore } from "@/store";

export default function ProfilePage() {
  return (
    <RequireAuth>
      <ProfileContent />
    </RequireAuth>
  );
}

function ProfileContent() {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return null;
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl items-center justify-center p-6">
      <section className="w-full max-w-xl space-y-5 rounded-xl border bg-card p-6 shadow-sm">
        <div>
          <p className="text-sm font-medium text-primary">Protected route</p>
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome back, {user.name}
          </h1>
        </div>

        <dl className="grid gap-3 rounded-lg border bg-muted/40 p-4 text-sm">
          <div>
            <dt className="font-medium">Email</dt>
            <dd className="text-muted-foreground">{user.email}</dd>
          </div>
          <div>
            <dt className="font-medium">Role</dt>
            <dd className="text-muted-foreground">{user.role || "Member"}</dd>
          </div>
        </dl>

        <div className="flex gap-3">
          <Button asChild variant="outline">
            <Link href={ROUTES.HOME}>Back home</Link>
          </Button>
          <LogoutButton />
        </div>

        <div className="border-t pt-4">
          <DeleteAccountButton />
        </div>
      </section>
    </div>
  );
}