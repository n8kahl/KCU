import clsx from "clsx";
import IndexConfluenceStrip from "./IndexConfluenceStrip";
import ManagingPanel from "./ManagingPanel";
import MTFMatrix from "./MTFMatrix";
import Sparkline from "./Sparkline";

type TileProps = {
  tile: any;
  onAction: (action: string) => void;
  onInspect: (tile: any) => void;
};

const bandStyles: Record<string, string> = {
  Loading: "bg-slate-800 text-slate-200",
  Armed: "bg-amber-600 text-black",
  EntryReady: "bg-emerald-500 text-black",
};

function TickerTile({ tile, onAction, onInspect }: TileProps) {
  const options = tile.options || {};
  const marketMicro = tile.admin?.marketMicro;
  const timing = tile.admin?.timing;
  const price = tile.admin?.lastPrice;
  const probabilityHistory = (tile.history || []).map((h: any) => (h.score ?? 0) / 100);
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-2xl">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">{tile.regime}</p>
          <div className="flex items-baseline gap-3">
            <h2 className="text-3xl font-semibold text-white">{tile.symbol}</h2>
            {price && <span className="text-lg text-slate-300">${price.toFixed(2)}</span>}
          </div>
          {timing?.label && <p className="text-xs text-slate-500">{timing.label} · TF {timing.tf_primary}</p>}
        </div>
        <span className={clsx("rounded-full px-3 py-1 text-xs font-semibold", bandStyles[tile.band?.label] || "bg-slate-800")}>{tile.band?.label}</span>
      </div>
      <div className="mt-4 grid gap-4 text-sm text-slate-200 md:grid-cols-3">
        <div>
          <p className="text-xs uppercase text-slate-500">Prob → Action</p>
          <p className="text-4xl font-semibold">{Math.round((tile.probability_to_action ?? 0) * 100)}%</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-500">Confidence p95</p>
          <p className="text-2xl font-semibold">{Math.round((tile.confidence?.p95 ?? 0) * 100)}%</p>
        </div>
        <div>
          <p className="text-xs uppercase text-slate-500">ETA</p>
          <p className="text-2xl font-semibold">{tile.eta_seconds ? `${tile.eta_seconds}s` : "--"}</p>
        </div>
      </div>
      <div className="mt-4">
        <Sparkline data={probabilityHistory} />
      </div>
      <div className="mt-4">
        <IndexConfluenceStrip market={marketMicro} orb={tile.admin?.orb} />
      </div>
      <div className="mt-4">
        <MTFMatrix breakdown={tile.breakdown} history={tile.history} />
      </div>
      <div className="mt-4 grid gap-3 text-xs md:grid-cols-2">
        <StatChip label="Spread" value={`${options.spread_pct ?? "--"}% (${options.spread_percentile_label || "p--"})`} />
        <StatChip label="NBBO" value={options.nbbo || "--"} />
        <StatChip label="Flicker" value={`${options.flicker_per_sec ?? "--"}/s`} />
        <StatChip label="Liquidity" value={options.liquidity_risk ?? "--"} tone={options.liquidity_risk >= 70 ? "bad" : "good"} />
      </div>
      <div className="mt-4 text-xs text-slate-300">
        <p className="text-emerald-300">{(tile.rationale?.positives || []).join(" · ")}</p>
        <p className="mt-1 text-rose-300">{(tile.rationale?.risks || []).join(" · ")}</p>
      </div>
      <ManagingPanel plan={tile.admin?.managing} />
      <div className="mt-4 flex flex-wrap gap-2 text-sm">
        <button className="flex-1 rounded bg-slate-800 py-2" onClick={() => onAction("snooze")}>
          Snooze
        </button>
        <button className="flex-1 rounded bg-slate-800 py-2" onClick={() => onAction("kill")}>
          Kill
        </button>
        <button className="flex-1 rounded bg-emerald-700 py-2" onClick={() => onAction("confirm")}>
          Confirm
        </button>
        <button className="w-full rounded border border-emerald-600 py-2 text-emerald-200" onClick={() => onInspect(tile)}>
          View details
        </button>
      </div>
    </div>
  );
}

function StatChip({ label, value, tone = "neutral" }: { label: string; value: string | number; tone?: "good" | "bad" | "neutral" }) {
  return (
    <div
      className={clsx(
        "rounded-lg px-3 py-2",
        tone === "good" && "bg-emerald-900/40 text-emerald-100",
        tone === "bad" && "bg-rose-900/40 text-rose-100",
        tone === "neutral" && "bg-slate-950/40 text-slate-200",
      )}
    >
      <p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  );
}

export default TickerTile;
