import { useEffect, useState } from "react";
import clsx from "clsx";
import { useTrades } from "../store/trades";

const ACTION_LABELS = ["Enter Trade", "Trim", "Take Profit", "Add", "Exit"] as const;
const KEY_BINDINGS: Record<string, (typeof ACTION_LABELS)[number]> = {
  e: "Enter Trade",
  t: "Trim",
  p: "Take Profit",
  a: "Add",
  x: "Exit",
};

function ActionButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button className="rounded bg-slate-800 px-2 py-1 text-[11px] text-slate-200 transition hover:bg-slate-700" onClick={onClick}>
      {label}
    </button>
  );
}

function ActiveTrades() {
  const { loaded, remove, clear } = useTrades();
  const [actionFeedback, setActionFeedback] = useState<string>("");

  const handleAction = (action: string, contractId: string) => {
    const trade = loaded.find((item) => item.contractId === contractId);
    if (!trade) return;
    setActionFeedback(`${action} on ${trade.label}`);
    // Future: hook into backend/Discord
  };

  const primaryTrade = loaded[0];

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const action = KEY_BINDINGS[event.key.toLowerCase()];
      if (!action || !primaryTrade) return;
      event.preventDefault();
      handleAction(action, primaryTrade.contractId);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [primaryTrade]);

  return (
    <aside className="w-full rounded-2xl border border-slate-800 bg-slate-950/60 p-4 lg:sticky lg:top-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Active Trades</p>
          <p className="text-lg font-semibold text-white">{loaded.length || "None"}</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="inline-flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <button className="text-slate-400 hover:text-white" onClick={clear} disabled={!loaded.length}>
            Kill All
          </button>
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {loaded.map((contract, index) => (
          <div
            key={contract.contractId}
            className={clsx(
              "rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-sm text-slate-200",
              index === 0 && "ring-2 ring-emerald-500/40",
            )}
          >
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>{contract.ticker}</span>
              <button onClick={() => remove(contract.contractId)} className="text-slate-500 hover:text-white">
                ×
              </button>
            </div>
            <p className="mt-1 font-mono text-[13px] text-slate-200">{contract.label}</p>
            <p className="mt-1 text-xs text-slate-400">
              Δ {contract.delta?.toFixed(2) ?? "--"} · DTE {contract.dte ?? "--"} · Mid {contract.mid ? `$${contract.mid.toFixed(2)}` : "--"} · Spr {contract.spreadPct?.toFixed(1) ?? "--"}%
            </p>
            <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5">
              {ACTION_LABELS.map((label) => (
                <ActionButton key={label} label={label} onClick={() => handleAction(label, contract.contractId)} />
              ))}
            </div>
          </div>
        ))}
        {!loaded.length && <p className="rounded border border-dashed border-slate-800 p-4 text-center text-xs text-slate-400">Load a contract from any tile to stage it here.</p>}
        {actionFeedback && <p className="text-center text-[11px] text-emerald-300">{actionFeedback}</p>}
      </div>
    </aside>
  );
}

export default ActiveTrades;
