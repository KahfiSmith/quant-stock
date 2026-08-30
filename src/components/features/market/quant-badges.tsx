import type { VolatilityRegime } from "@/types";

type VolumeAnomalyBadgeProps = {
  zscore: number | null | undefined;
};

type BadgeConfig = { label: string; className: string };

const THRESHOLDS = {
  spike: { min: 2.0, label: "Volume Spike", className: "bg-amber-500/10 text-amber-600 dark:text-amber-400" },
  high: { min: 1.5, label: "High Volume", className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" },
  low: { max: -1.0, label: "Low Volume", className: "bg-rose-500/10 text-rose-600 dark:text-rose-400" },
  normal: { label: "Normal", className: "bg-muted text-muted-foreground" },
};

export function VolumeAnomalyBadge({ zscore }: VolumeAnomalyBadgeProps) {
  if (zscore == null) return null;

  let config: BadgeConfig = THRESHOLDS.normal;
  if (zscore >= THRESHOLDS.spike.min) config = THRESHOLDS.spike;
  else if (zscore >= THRESHOLDS.high.min) config = THRESHOLDS.high;
  else if (zscore <= THRESHOLDS.low.max) config = THRESHOLDS.low;

  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${config.className}`}>
      {config.label}
      <span className="font-mono text-[10px] opacity-75">Z={zscore.toFixed(1)}</span>
    </span>
  );
}

type VolatilityRegimeBadgeProps = {
  regime: VolatilityRegime | string | null | undefined;
  atrPercent?: number | null;
};

const REGIME_CONFIG: Record<string, { label: string; className: string }> = {
  LOW: { label: "Low Vol", className: "bg-sky-500/10 text-sky-600 dark:text-sky-400" },
  NORMAL: { label: "Normal Vol", className: "bg-muted text-muted-foreground" },
  HIGH: { label: "High Vol", className: "bg-amber-500/10 text-amber-600 dark:text-amber-400" },
  EXTREME: { label: "Extreme Vol", className: "bg-red-500/10 text-red-600 dark:text-red-400" },
};

export function VolatilityRegimeBadge({ regime, atrPercent }: VolatilityRegimeBadgeProps) {
  if (!regime) return null;

  const config = REGIME_CONFIG[regime] ?? REGIME_CONFIG.NORMAL;

  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${config.className}`}>
      {config.label}
      {atrPercent != null && (
        <span className="font-mono text-[10px] opacity-75">{atrPercent.toFixed(1)}%</span>
      )}
    </span>
  );
}
