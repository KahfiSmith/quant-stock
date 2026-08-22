import { ROUTES } from "@/config/routes";

export function getSafeRedirect(target: string | null | undefined): string {
  if (!target || !target.startsWith("/") || target.startsWith("//")) {
    return ROUTES.PROFILE;
  }

  return target;
}
