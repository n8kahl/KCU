import clsx from "clsx";
import { useMemo } from "react";
import MiniCandles from "./MiniCandles";
import type { Tile } from "../types";

type Props = {
  tile: Tile & { updatedAt?: number };
  now: number;
  onExpand: (tile: Tile) => void;
};

function formatDelta(delta?: Tile["delta_to_entry"]) {
  if (!delta) return "--";
  const dollars = delta.dollars ? `${delta.dollars > 0 ? "+" : ""}${delta.dollars.toFixed(2)}$` : "--";
  const percent = delta.percent ? `${delta.percent > 0 ? "+" : ""}${delta.percent.toFixed(2)}%` : "--";
  return `${dollars} / ${percent}`;
}

const numberList = (values: Array<number | null | undefined>): number[] =>
  values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));

export default function TickerCard({ tile, now, onExpand }: Props) {
  const price = tile.admin?.lastPrice;
  const probability = Math.round((tile.probability_to_action ?? 0) * 100);
  const confidence = tile.confidence_score ?? Math.round((tile.confidence?.p95 ?? 0) * 100);
  const updatedAt = tile.updatedAt ?? Date.parse(tile.timestamps?.updated ?? "");
  const timeAgo = Number.isFinite(updatedAt) ? Math.max(0, Math.round((now - updatedAt) / 1000)) : 0;
  const entryReady = Boolean(tile.delta_to_entry?.at_entry && tile.patience_candle);
  const rationale = tile.rationale?.positives?.[0] ?? "Watching flow";
  const confluenceLeaders = useMemo(() => tile.breakdown.slice(0, 2), [tile.breakdown]);
  const closes =
    (Array.isArray(tile.admin?.last_1m_closes) && tile.admin?.last_1m_closes?.length ? tile.admin?.last_1m_closes : numberList((tile.bars ?? []).map((bar) => bar.c ?? bar.o))).slice();
  const keyLevels = (tile.key_levels?.length ? tile.key_levels : tile.admin?.levels) ?? [];
  const patienceCue = (tile.admin?.timing?.label ?? "").toLowerCase().includes("patience");
  const entryBand = (tile.band?.label ?? "").toLowerCase() === "entryready".toLowerCase();
  const isAGrade = (tile.grade || "").toUpperCase().startsWith("A");
  const aPlusEntry = (entryBand && isAGrade) || patienceCue;

  return (
    <article className="flex flex-col gap-4 rounded-2xl border border-slate-800/80 bg-slate-950/60 p-4 shadow-lg transition hover:border-emerald-500/50">
      <header className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <p className="text-2xl font-semibold text-white">{tile.symbol}</p>
            <span className="rounded-full border border-slate-700 px-2 py-0.5 text-xs uppercase tracking-wide text-slate-300">{tile.band?.label ?? ""}</span>
          </div>
          <p className="mt-1 text-sm text-slate-400">{timeAgo}s ago · {rationale}</p>
        </div>
        <div className="text-right">
          <p className="text-sm uppercase text-slate-500">Grade</p>
          <p className="text-xl font-semibold text-white">{tile.grade}</p>
          <p className="text-xs text-slate-500">Conf {confidence}%</p>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <div>
          <p className="text-xs uppercase text-slate-500">Price</p>
          <p className="text-2xl font-semibold text-white">{price ? `$${price.toFixed(2)}` : "--"}</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-500">Δ to Entry</p>
          <p className={clsx("text-lg font-semibold", entryReady ? "text-emerald-300" : "text-slate-100")}>{formatDelta(tile.delta_to_entry)}</p>
          <p className="text-[11px] text-slate-500">{tile.key_level_label ?? "No level"}</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-500">Prob to Act</p>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-semibold text-white">{probability}%</span>
            <span className="text-xs text-slate-500">{tile.regime}</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-2 rounded-2xl border border-slate-800/60 bg-slate-900/30 p-3">
        <p className="text-xs uppercase tracking-wide text-slate-500">Micro structure</p>
        <MiniCandles
          closes={closes}
          levels={keyLevels}
          managing={tile.admin?.managing}
          ema={{ e8: tile.ema8, e21: tile.ema21 }}
          aPlusEntry={aPlusEntry}
        />
        <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
          <span className={clsx("rounded-full px-2 py-0.5", tile.patience_candle ? "bg-emerald-600/20 text-emerald-200" : "bg-slate-800 text-slate-400")}>Patience {tile.patience_candle ? "On" : "Off"}</span>
          <span>VWAP {tile.vwap[tile.vwap.length - 1]?.toFixed(2) ?? "--"}</span>
          <span>EMA8 {tile.ema8[tile.ema8.length - 1]?.toFixed(2) ?? "--"}</span>
          <span>EMA21 {tile.ema21[tile.ema21.length - 1]?.toFixed(2) ?? "--"}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-slate-300">
        {confluenceLeaders.map((item) => (
          <div key={item.name} className="rounded-lg border border-slate-800/80 px-3 py-2">
            <p className="text-[11px] uppercase text-slate-500">{item.name}</p>
            <p className="text-lg font-semibold">{Math.round(item.score * 100)}%</p>
          </div>
        ))}
        <div className="rounded-lg border border-slate-800/80 px-3 py-2">
          <p className="text-[11px] uppercase text-slate-500">Options</p>
          <p>{tile.options_top3.length ? `${tile.options_top3.length} OTM ready` : "Options warming…"}</p>
        </div>
      </div>

      <button
        className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/20"
        onClick={() => onExpand(tile)}
      >
        Expand details
      </button>
    </article>
  );
}
