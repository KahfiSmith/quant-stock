import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";

type StateMessageProps = {
  variant: "loading" | "error" | "empty";
  children?: ReactNode;
};

const BOX_STYLES = {
  error: "border-destructive/40 bg-destructive/10 text-destructive",
  empty: "border bg-muted/40 text-muted-foreground",
} as const;

export function StateMessage({ variant, children }: StateMessageProps) {
  if (variant === "loading") {
    return (
      <div className="flex items-center justify-center p-6 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className={`rounded-lg border p-4 text-left text-sm ${BOX_STYLES[variant]}`}>
      {children}
    </div>
  );
}