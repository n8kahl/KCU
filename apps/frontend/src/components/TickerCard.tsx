import clsx from "clsx";
import { ReactNode, useEffect, useMemo, useState } from "react";
import { formatContractId } from "../lib/format";
import { useTrades } from "../store/trades";

interface TilePayload {
  symbol: string;
  updatedAt: number;
  price?: number;
  regime?: string;
  probability_to_action?: number;
  confidence?: { p95?: number };
  eta_seconds?: number | null;
  etaSeconds?: number | null;
  band?: { label?: string; min_score?: number; max_score?: number };
  admin?: Record<string, any>;
  options?: Record<string, any>;
  breakdown?: { name: string; score: number }[];
}

function microChopLabel(value: number | undefined) {
  if (value === undefined || value === null) return "--";
  if (value < 0.3) return "Low";
  if (value < 0.6) return "Med";
  return "High";
}

function usePulseTrigger(value: number) {
  const [pulse, setPulse] = useState(false);
  useEffect(() => {
    setPulse(true);
    const timer = setTimeout(() => setPulse(false), 1200);
    return () => clearTimeout(timer);
  }, [value]);
  return pulse;
}

function useLevelDistance(admin: any, lastPrice: number | undefined) {
  return useMemo(() => {
    if (!lastPrice || !admin?.levels?.length) return null;
    let best: { label: string; price: number; dist: number } | null = null;
    for (const level of admin.levels) {
      if (typeof level?.price !== "number" || !level.label) continue;
      const dist = Math.abs(level.price - lastPrice);
      if (!best || dist < best.dist) {
        best = { label: level.label, price: level.price, dist, rawDiff: level.price - lastPrice } as any;
      }
    }
    return best;
  }, [admin, lastPrice]);
}

function calcMtfPills(closes: number[] | undefined) {
  const frames = [2, 5, 15, 60, 120];
  if (!closes?.length) return frames.map((tf) => ({ tf: labelForTf(tf), positive: false }));
  return frames.map((window) => {
    if (closes.length < window) return { tf: labelForTf(window), positive: false };
    const slice = closes.slice(-window);
    const diff = slice[slice.length - 1] - slice[0];
    return { tf: labelForTf(window), positive: diff >= 0 };
  });
}

function labelForTf(minutes: number) {
  if (minutes >= 120) return "Daily";
  if (minutes >= 60) return "60m";
  return `${minutes}m`;
}

function calcVolumeTrend(closes: number[] | undefined) {
  if (!closes || closes.length < 6) return "--";
  const recent = closes.slice(-3);
  const base = closes.slice(-6, -3);
  if (!base.length) return "--";
  const avgRecent = recent.reduce((acc, cur) => acc + cur, 0) / recent.length;
  const avgBase = base.reduce((acc, cur) => acc + cur, 0) / base.length;
  const ratio = avgRecent / avgBase;
  if (!Number.isFinite(ratio)) return "--";
  if (ratio > 1.02) return "High";
  if (ratio < 0.98) return "Low";
  return "Avg";
}

function MiniSparkline({ values, level }: { values?: number[]; level?: number | null }) {
  if (!values || values.length < 2) {
    return <div className="h-12 w-full rounded border border-slate-800 bg-slate-950/40 text-center text-[10px] text-slate-500">No data</div>;
  }
  const recent = values.slice(-16);
  const min = Math.min(...recent);
  const max = Math.max(...recent);
  const span = max - min || 1;
  const points = recent
    .map((value, index) => {
      const x = (index / (recent.length - 1)) * 100;
      const y = ((max - value) / span) * 40;
      return `${x},${y}`;
    })
    .join(" ");
  const levelY = level ? ((max - level) / span) * 40 : null;
  return (
    <svg viewBox="0 0 100 40" className="h-12 w-full">
      {levelY !== null && levelY >= 0 && levelY <= 40 && (
        <line x1="0" y1={levelY} x2="100" y2={levelY} stroke="#64748b" strokeDasharray="4 3" strokeWidth="0.6" />
      )}
      <polyline points={points} fill="none" stroke="#34d399" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function ContractsList({ tile }: { tile: TilePayload }) {
  const options = tile.options || {};
  const contracts = [options.contracts?.primary, ...(options.contracts?.backups || [])].filter(Boolean);
  const trades = useTrades();
  if (!contracts.length) return <p className="text-xs text-slate-500">No contracts provided.</p>;
  const meta = {
    delta: options.delta_target,
    dte: options.dte_days,
    spreadPct: options.spread_pct,
    nbbo: options.nbbo,
    mid: options.mid,
  };
  return (
    <div className="space-y-2">
      {contracts.slice(0, 6).map((contractId: string, index: number) => (
        <div key={contractId} className="flex items-center justify-between rounded border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs">
          <div>
            <p className="font-mono text-[12px] text-slate-200">
              {index < 2 ? "ITM" : "OTM"} · {formatContractId(contractId)}
            </p>
            <p className="text-[11px] text-slate-400">
              Δ {meta.delta?.toFixed(2) ?? "--"} · DTE {meta.dte ?? "--"} · Spr {meta.spreadPct?.toFixed(1) ?? "--"}% · NBBO {meta.nbbo ?? "--"}
            </p>
          </div>
          <button
            className="rounded bg-emerald-600 px-3 py-1 text-[11px] font-semibold text-emerald-50 hover:bg-emerald-500"
            onClick={() =>
              trades.add({
                ticker: tile.symbol,
                contractId,
                label: formatContractId(contractId),
                delta: meta.delta,
                dte: meta.dte,
                spreadPct: meta.spreadPct,
                mid: meta.mid,
              })
            }
          >
            Load
          </button>
        </div>
      ))}
    </div>
  );
}

function BreakdownGrid({ breakdown }: { breakdown?: { name: string; score: number }[] }) {
  if (!breakdown?.length) return null;
  return (
    <div className="grid grid-cols-2 gap-2">
      {breakdown.map((row) => (
        <div key={row.name} className="flex items-center justify-between rounded bg-slate-900/50 px-3 py-2 text-xs">
          <span>{row.name}</span>
          <span className="font-semibold">{Math.round(row.score * 100)}%</span>
        </div>
      ))}
    </div>
  );
}

type Props = {
  tile: TilePayload;
  now: number;
};

export default function TickerCard({ tile, now }: Props) {
  const lastPrice = tile.admin?.lastPrice ?? tile.price;
  const prob = Math.round((tile.probability_to_action ?? 0) * 100);
  const confidence = Math.round((tile.confidence?.p95 ?? 0) * 100);
  const eta = tile.eta_seconds ?? tile.etaSeconds;
  const band = tile.band;
  const bandMin = band?.min_score ?? 0;
  const bandMax = band?.max_score ?? 100;
  const relativeScore = Math.min(1, Math.max(0, (prob - bandMin) / Math.max(1, bandMax - bandMin)));
  const micro = tile.admin?.marketMicro || {};
  const mtfCloses = tile.admin?.last_1m_closes as number[] | undefined;
  const mtf = useMemo(() => calcMtfPills(mtfCloses), [mtfCloses]);
  const levelInfo = useLevelDistance(tile.admin, lastPrice);
  const volumeTrend = calcVolumeTrend(mtfCloses);
  const timeAgo = Math.max(0, Math.round((now - tile.updatedAt) / 1000));
  const pulse = usePulseTrigger(tile.updatedAt);

  return (
    <article className="flex flex-col rounded-2xl border border-slate-800 bg-slate-900/60 p-4 shadow-lg transition">
      <div className="flex items-center justify-between text-sm text-slate-300">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xl font-semibold text-white">{tile.symbol}</span>
          {lastPrice && <span>${lastPrice.toFixed(2)}</span>}
          <span className="text-xs text-slate-500">{timeAgo}s ago</span>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-200">{band?.label || tile.regime || ""}</span>
          <span className={clsx("h-2 w-2 rounded-full", pulse ? "bg-emerald-400 animate-pulse" : "bg-slate-600")} />
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <p className="text-xs uppercase text-slate-400">Probability → Action</p>
          <p className="text-3xl font-semibold">{prob}%</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-400">Confidence p95</p>
          <p className="text-2xl font-semibold">{confidence}%</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-400">ETA</p>
          <p className="text-2xl font-semibold">{eta ? `${eta}s` : "—"}</p>
        </div>
      </div>
      <div className="mt-3 h-1.5 rounded bg-slate-800">
        <div className="h-full rounded bg-emerald-500 transition-all" style={{ width: `${relativeScore * 100}%` }} />
      </div>

      <div className="mt-4 grid gap-2 text-xs text-slate-200 sm:grid-cols-3">
        <InfoChip label="Key level" value={levelInfo ? `${levelInfo.label} · ${(levelInfo.price - (lastPrice ?? 0)).toFixed(2)}` : "—"} />
        <InfoChip label="Trend" value={mtf.filter((pill) => pill.positive).length >= 3 ? "Stacked" : "Mixed"} />
        <InfoChip label="Volume" value={volumeTrend} />
        <InfoChip
          label="MTF"
          value={
            <div className="flex flex-wrap gap-1">
              {mtf.map((pill) => (
                <span key={pill.tf} className={clsx("rounded px-1.5 py-0.5 text-[10px]", pill.positive ? "bg-emerald-700/40 text-emerald-200" : "bg-slate-800 text-slate-400")}>{pill.tf}</span>
              ))}
            </div>
          }
        />
        <InfoChip label="Thrust" value={micro.minuteThrust && micro.minuteThrust > 0 ? "✓" : "✗"} />
        <InfoChip label="Micro-chop" value={microChopLabel(micro.microChop)} />
        <InfoChip label="ETF vs IDX" value={`${(micro.divergenceZ ?? 0).toFixed(2)}σ`} />
        <InfoChip label="ORB % ADR" value={`${Math.round((tile.admin?.orb?.range_pct ?? 0) * 100)}%`} />
      </div>

      <details className="group mt-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
        <summary className="flex cursor-pointer items-center justify-between text-sm font-semibold text-white marker:hidden">
          <span>Contracts & detail</span>
          <span className="text-xs text-slate-400 group-open:rotate-180">▾</span>
        </summary>
        <div className="mt-3 space-y-4">
          <section>
            <div className="text-xs uppercase tracking-wide text-slate-400">Top contracts</div>
            <ContractsList tile={tile} />
          </section>
          <section>
            <div className="text-xs uppercase tracking-wide text-slate-400">Confluence</div>
            <BreakdownGrid breakdown={tile.breakdown} />
          </section>
          <section className="grid gap-3 text-xs text-slate-300 sm:grid-cols-2">
            <InfoChip label="Spread" value={`${tile.options?.spread_pct ?? "--"}% (${tile.options?.spread_percentile_label || "p--"})`} />
            <InfoChip label="NBBO" value={tile.options?.nbbo || "--"} />
            <InfoChip label="Flicker" value={`${tile.options?.flicker_per_sec ?? "--"}/s`} />
            <InfoChip label="Liquidity" value={tile.options?.liquidity_risk ?? "--"} />
          </section>
          <section>
            <MiniSparkline values={mtfCloses} level={levelInfo?.price ?? null} />
          </section>
        </div>
      </details>
    </article>
  );
}

function InfoChip({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-sm text-slate-200">{value}</p>
    </div>
  );
}
