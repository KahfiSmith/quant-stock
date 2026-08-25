"use client";

import { LoginForm } from "@/components/features/auth/login-form";
import { RedirectAuthenticated } from "@/components/features/auth/route-guards";

export default function LoginPage() {
  return (
    <RedirectAuthenticated>
      <LoginForm />
    </RedirectAuthenticated>
  );
}