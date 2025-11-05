import { useMemo, useState } from "react";
import clsx from "clsx";
import { postAlert } from "../api/client";
import { useTrades } from "../store/trades";
import type { ActiveTrade, AlertPayload } from "../types";

const ACTION_LABELS: Record<string, string> = {
  enter: "Enter",
  add: "Add",
  take_profit: "Take Profit",
  trim: "Trim",
  exit: "Exit",
};

export default function ActiveTrades() {
  const trades = useTrades((state) => state.trades);
  const remove = useTrades((state) => state.remove);
  const clear = useTrades((state) => state.clear);
  const closeTrade = useTrades((state) => state.close);
  const recordAlert = useTrades((state) => state.recordAlert);
  const reAlertTemplate = useTrades((state) => state.reAlertTemplate);
  const [reAlerting, setReAlerting] = useState<string | null>(null);

  const openTrades = useMemo(() => trades.filter((trade) => !trade.isClosed), [trades]);

  const handleReAlert = async (trade: ActiveTrade) => {
    const template = reAlertTemplate(trade.contractId);
    if (!template) return;
    setReAlerting(trade.contractId);
    const priceBase = trade.latestMid ?? template.price;
    if (!priceBase) {
      setReAlerting(null);
      return;
    }
    const payload: AlertPayload = {
      ...template,
      price: Number(priceBase.toFixed(2)),
    };
    try {
      await postAlert(payload);
      recordAlert(trade.contractId, payload);
    } finally {
      setReAlerting(null);
    }
  };

  return (
    <aside className="w-full rounded-2xl border border-slate-800 bg-slate-950/60 p-4 lg:sticky lg:top-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Active Trades</p>
          <p className="text-lg font-semibold text-white">{openTrades.length || "None"}</p>
        </div>
        <button className="text-xs text-slate-400 hover:text-white" onClick={clear} disabled={!trades.length}>
          Kill All
        </button>
      </div>
      <div className="mt-4 space-y-4">
        {trades.map((trade) => (
          <div key={trade.contractId} className={clsx("rounded-2xl border p-4", trade.isClosed ? "border-slate-800 bg-slate-900/40" : "border-emerald-500/40 bg-emerald-500/5")}
          >
            <div className="flex items-center justify-between text-sm">
              <div>
                <p className="font-mono text-base text-white">{trade.contract.contract}</p>
                <p className="text-xs text-slate-400">{trade.symbol} · {trade.contract.expiry ?? "--"} · {trade.contract.type?.toUpperCase() ?? "--"}</p>
              </div>
              <button className="text-slate-500 hover:text-white" onClick={() => remove(trade.contractId)}>
                ×
              </button>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-3 text-sm text-slate-300">
              <div>
                <p className="text-[11px] uppercase text-slate-500">Entry</p>
                <p>{trade.entryPrice ? `$${trade.entryPrice.toFixed(2)}` : "--"}</p>
              </div>
              <div>
                <p className="text-[11px] uppercase text-slate-500">Mid</p>
                <p>{trade.latestMid ? `$${trade.latestMid.toFixed(2)}` : "--"}</p>
              </div>
              <div>
                <p className="text-[11px] uppercase text-slate-500">%PnL</p>
                <p className={clsx(trade.pnlPct && trade.pnlPct >= 0 ? "text-emerald-300" : "text-rose-300")}>{trade.pnlPct?.toFixed(2) ?? "--"}%</p>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
              <span>Δ {trade.contract.delta?.toFixed(2) ?? "--"}</span>
              <span>OI {trade.contract.oi ?? "--"}</span>
              <span>DTE {trade.contract.expiry ?? "--"}</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <button className="rounded-full border border-slate-700 px-3 py-1 text-slate-200" onClick={() => handleReAlert(trade)} disabled={!trade.lastTemplate || reAlerting === trade.contractId}>
                {reAlerting === trade.contractId ? "Sending…" : "Re-alert"}
              </button>
              <button className="rounded-full border border-slate-700 px-3 py-1 text-slate-200" onClick={() => closeTrade(trade.contractId)} disabled={trade.isClosed}>
                Close & Log
              </button>
            </div>
            <div className="mt-4 space-y-2">
              {trade.timeline.length ? (
                trade.timeline.slice(-3).map((alert) => (
                  <div key={alert.id} className="rounded-xl border border-slate-800/70 bg-slate-950/40 px-3 py-2 text-xs text-slate-300">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold text-white">{ACTION_LABELS[alert.action] ?? alert.action}</p>
                      <span>{new Date(alert.createdAt).toLocaleTimeString()}</span>
                    </div>
                    <p>Grade {alert.grade} · Conf {alert.confidence}% · @{alert.price?.toFixed(2) ?? "--"}</p>
                    {alert.note && <p className="text-slate-400">{alert.note}</p>}
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500">No alerts logged.</p>
              )}
            </div>
          </div>
        ))}
        {!trades.length && <p className="rounded border border-dashed border-slate-800/70 p-4 text-center text-sm text-slate-500">Load a contract from any tile to stage it here.</p>}
      </div>
    </aside>
  );
}
