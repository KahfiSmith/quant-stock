"use client";

import { useState } from "react";
import { toast } from "sonner";

import { RequireAuth } from "@/components/features/auth";
import { useUpdateProfile } from "@/hooks/auth";
import { useAuthStore } from "@/store";

export default function SettingsPage() {
  return (
    <RequireAuth>
      <SettingsContent />
    </RequireAuth>
  );
}

function SettingsContent() {
  const user = useAuthStore((state) => state.user);
  const updateProfile = useUpdateProfile();
  const [name, setName] = useState(user?.name ?? "");
  const [theme, setTheme] = useState<"light" | "dark" | "system">(user?.theme_preference ?? "system");
  const [timezone, setTimezone] = useState(user?.timezone ?? "UTC");

  if (!user) return null;

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await updateProfile.mutateAsync({ name, theme_preference: theme, timezone });
      toast.success("Settings updated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update settings");
    }
  };

  return (
    <main className="mx-auto w-full max-w-xl p-6">
      <form onSubmit={save} className="space-y-5 rounded-xl border bg-card p-6 shadow-sm">
        <div>
          <p className="text-sm font-medium text-primary">Account settings</p>
          <h1 className="text-2xl font-semibold">Profile preferences</h1>
        </div>
        <label className="grid gap-2 text-sm">Display name<input className="rounded-md border bg-background px-3 py-2" value={name} onChange={(event) => setName(event.target.value)} minLength={2} required /></label>
        <label className="grid gap-2 text-sm">Theme<select className="rounded-md border bg-background px-3 py-2" value={theme} onChange={(event) => setTheme(event.target.value as typeof theme)}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
        <label className="grid gap-2 text-sm">Timezone<input className="rounded-md border bg-background px-3 py-2" value={timezone} onChange={(event) => setTimezone(event.target.value)} required /></label>
        <button type="submit" disabled={updateProfile.isPending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">Save settings</button>
      </form>
    </main>
  );
}
