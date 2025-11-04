import { Fragment } from "react";
import IndexConfluenceStrip from "./IndexConfluenceStrip";
import ManagingPanel from "./ManagingPanel";
import MTFMatrix from "./MTFMatrix";
import WhatIfPanel from "./WhatIfPanel";

function DetailDrawer({ tile, onClose }: { tile: any; onClose: () => void }) {
  if (!tile) return null;
  const breakdown = tile.breakdown || [];
  const options = tile.options || {};
  const contracts = options.contracts || {};
  const marketMicro = tile.admin?.marketMicro;
  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="flex-1 bg-black/60" onClick={onClose} />
      <aside className="flex w-full max-w-3xl flex-col overflow-y-auto bg-slate-950 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase text-slate-500">Now</p>
            <h2 className="text-2xl font-semibold text-white">{tile.symbol}</h2>
            <p className="text-sm text-slate-400">{tile.admin?.timing?.label}</p>
          </div>
          <button className="rounded bg-slate-800 px-3 py-1 text-sm" onClick={onClose}>
            Close
          </button>
        </div>
        <section className="mt-6 space-y-3">
          <div className="grid grid-cols-2 gap-4 text-sm text-slate-200">
            <div>
              <p className="text-xs uppercase text-slate-500">Probability</p>
              <p className="text-2xl font-semibold">{Math.round((tile.probability_to_action ?? 0) * 100)}%</p>
            </div>
            <div>
              <p className="text-xs uppercase text-slate-500">Confidence p95</p>
              <p className="text-2xl font-semibold">{Math.round((tile.confidence?.p95 ?? 0) * 100)}%</p>
            </div>
          </div>
          <MTFMatrix breakdown={breakdown} history={tile.history} />
          <IndexConfluenceStrip market={marketMicro} orb={tile.admin?.orb} />
        </section>
        <section className="mt-6 rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-200">
          <h3 className="text-sm font-semibold text-white">Confluence breakdown</h3>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            {breakdown.map((row: any) => (
              <div key={row.name} className="flex items-center justify-between rounded bg-slate-950/50 px-3 py-2">
                <span>{row.name}</span>
                <span className="font-semibold">{Math.round(row.score * 100)}%</span>
              </div>
            ))}
          </div>
        </section>
        <section className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-200">
            <h3 className="text-sm font-semibold text-white">Options health</h3>
            <ul className="mt-3 space-y-2 text-xs">
              <li>Spread {options.spread_pct}% ({options.spread_percentile_label || "p--"})</li>
              <li>NBBO {options.nbbo}</li>
              <li>Flicker {options.flicker_per_sec ?? "--"}/s ({options.flicker_label || "p--"})</li>
              <li>Liquidity risk {options.liquidity_risk ?? "--"}</li>
            </ul>
            <div className="mt-4 text-xs">
              <p className="text-slate-400">Play-along contracts</p>
              <ul className="mt-2 space-y-1">
                {[contracts.primary, ...(contracts.backups || [])]
                  .filter(Boolean)
                  .map((contract: string) => (
                    <li key={contract} className="rounded bg-slate-950/50 px-2 py-1 font-mono text-[11px]">
                      {contract}
                    </li>
                  ))}
              </ul>
            </div>
          </div>
          <ManagingPanel plan={tile.admin?.managing} />
        </section>
        <section className="mt-6 grid gap-4 md:grid-cols-2">
          <WhatIfPanel ticker={tile.symbol} />
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-200">
            <h3 className="text-sm font-semibold text-white">Why / Why not</h3>
            <div className="mt-2 text-xs">
              <p className="text-emerald-300">{(tile.rationale?.positives || []).join(" · ")}</p>
              <p className="mt-1 text-rose-300">{(tile.rationale?.risks || []).join(" · ")}</p>
            </div>
          </div>
        </section>
      </aside>
    </div>
  );
}

export default DetailDrawer;
