import { clsx } from "clsx";

type TileProps = {
  tile: any;
  onAction: (action: string) => void;
};

const bandStyles: Record<string, string> = {
  Loading: "bg-slate-800",
  Armed: "bg-amber-600",
  EntryReady: "bg-emerald-600",
};

function TickerTile({ tile, onAction }: TileProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase text-slate-400">{tile.regime}</p>
          <h2 className="text-2xl font-semibold">{tile.symbol}</h2>
        </div>
        <span className={clsx("rounded-full px-3 py-1 text-xs font-semibold", bandStyles[tile.band?.label] || "bg-slate-700")}>
          {tile.band?.label}
        </span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-slate-400">Prob → Action</p>
          <p className="text-3xl font-bold">{Math.round(tile.probability_to_action * 100)}%</p>
        </div>
        <div>
          <p className="text-slate-400">Confidence</p>
          <p className="text-lg">p50 {tile.confidence?.p50}</p>
        </div>
      </div>
      <div className="mt-4 space-y-2 text-xs text-slate-300">
        <p>Reasons: {(tile.rationale?.positives || []).join(", ")}</p>
        <p>Risks: {(tile.rationale?.risks || []).join(", ")}</p>
      </div>
      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        {tile.options && (
          <span className="rounded bg-slate-800 px-2 py-1">Spread {tile.options.spread_pct}%</span>
        )}
        {tile.options && <span className="rounded bg-slate-800 px-2 py-1">IVR {tile.options.ivr}</span>}
        {tile.options && <span className="rounded bg-slate-800 px-2 py-1">Δ {tile.options.delta_target}</span>}
      </div>
      <div className="mt-4 flex gap-2 text-xs">
        <button className="flex-1 rounded bg-slate-800 py-2" onClick={() => onAction("snooze")}>
          Snooze
        </button>
        <button className="flex-1 rounded bg-slate-800 py-2" onClick={() => onAction("kill")}>
          Kill
        </button>
        <button className="flex-1 rounded bg-emerald-700 py-2" onClick={() => onAction("confirm")}>
          Confirm
        </button>
      </div>
    </div>
  );
}

export default TickerTile;
