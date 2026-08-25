"use client";

import { LoginForm, RedirectAuthenticated } from "@/components/features/auth";

export default function LoginPage() {
  return (
    <RedirectAuthenticated>
      <LoginForm />
    </RedirectAuthenticated>
  );
}