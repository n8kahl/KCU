import { useMemo, useState } from "react";
import clsx from "clsx";
import { postAlert } from "../api/client";
import { useTrades } from "../store/trades";
import type { AlertPayload, Contract, Tile } from "../types";
import MicroStructureChart from "./MicroStructureChart";

const ACTION_LABELS = {
  enter: "Enter",
  add: "Add",
  take_profit: "Take Profit",
  trim: "Trim",
  exit: "Exit",
} as const;

type Props = {
  tile: Tile;
  onClose: () => void;
};

function contractPrice(contract?: Contract) {
  if (!contract) return undefined;
  const candidates = [contract.mid, contract.ask, contract.bid];
  return candidates.find((value) => typeof value === "number" && value > 0);
}

function useTradeForContract(contractId: string | undefined, symbol: string) {
  return useTrades((state) => state.trades.find((trade) => trade.contractId === contractId) ?? state.trades.find((trade) => trade.symbol === symbol));
}

export default function DetailDrawer({ tile, onClose }: Props) {
  const loadContract = useTrades((state) => state.loadContract);
  const recordAlert = useTrades((state) => state.recordAlert);
  const trades = useTrades((state) => state.trades);
  const [activeAction, setActiveAction] = useState<AlertPayload["action"] | null>(null);
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [selectedContractId, setSelectedContractId] = useState<string>(tile.options_top3[0]?.contract ?? "");
  const selectedContract = tile.options_top3.find((option) => option.contract === selectedContractId) ?? tile.options_top3[0];
  const activeTrade = useTradeForContract(selectedContract?.contract, tile.symbol);
  const plan = tile.admin?.managing;
  const levelLabel = tile.key_level_label ?? plan?.tp1?.label ?? plan?.tp2?.label ?? "Key level";
  const stopPrice = plan?.runner?.trail ?? (plan?.entry && tile.admin?.atr ? plan.entry - tile.admin.atr : tile.admin?.atr ?? 0.5);
  const targetPrice = plan?.tp1?.price ?? plan?.entry ?? tile.admin?.lastPrice ?? 0;
  const entrySentence = useMemo(() => {
    const direction = plan?.direction ?? "long";
    const entry = plan?.entry ?? tile.admin?.lastPrice ?? 0;
    return `${tile.symbol} ${tile.grade} setup: ${direction} on ${levelLabel} with entry ${entry ? `$${entry.toFixed(2)}` : "--"}, stop ${stopPrice ? `$${stopPrice.toFixed(2)}` : "--"}, target ${targetPrice ? `$${targetPrice.toFixed(2)}` : "--"}.`;
  }, [plan, tile, levelLabel, stopPrice, targetPrice]);
  const metrics = [
    { label: "Trend", value: `${Math.round((tile.breakdown.find((row) => row.name === "TrendStack")?.score ?? 0) * 100)}%` },
    { label: "Chop", value: `${(tile.admin?.marketMicro?.microChop ?? 0).toFixed(2)}` },
    { label: "ORB", value: `${Math.round((tile.admin?.orb?.range_pct ?? 0) * 100)}% ADR` },
    { label: "VWAP", value: tile.vwap[tile.vwap.length - 1]?.toFixed(2) ?? "--" },
    { label: "EMA spread", value: `${tile.ema8[tile.ema8.length - 1]?.toFixed(2) ?? "--"} / ${tile.ema21[tile.ema21.length - 1]?.toFixed(2) ?? "--"}` },
    { label: "Timing", value: tile.admin?.timing?.label ?? "--" },
  ];

  const timeline = activeTrade?.timeline ?? [];
  const priceToSend = contractPrice(selectedContract);
  const canSend = Boolean(activeAction && selectedContract && priceToSend);

  const handleSend = async () => {
    if (!activeAction || !selectedContract || !priceToSend) return;
    const payload: AlertPayload = {
      action: activeAction,
      symbol: tile.symbol,
      contract: selectedContract.contract,
      price: Number(priceToSend.toFixed(2)),
      grade: tile.grade,
      confidence: tile.confidence_score ?? 0,
      level: levelLabel,
      stop: Number((stopPrice ?? 0).toFixed(2)),
      target: Number((targetPrice ?? 0).toFixed(2)),
      note: note || undefined,
    };
    setSending(true);
    try {
      await postAlert(payload);
      recordAlert(selectedContract.contract, payload);
      setActiveAction(null);
      setNote("");
    } finally {
      setSending(false);
    }
  };

  const handleLoad = (contract: Contract) => {
    setSelectedContractId(contract.contract);
    loadContract(tile.symbol, contract);
  };

  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="flex-1 bg-black/60" onClick={onClose} />
      <aside className="glass-panel flex w-full max-w-4xl flex-col overflow-y-auto bg-slate-950/90 p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs uppercase text-slate-500">Now</p>
            <h2 className="text-3xl font-semibold text-white">{tile.symbol}</h2>
            <p className="text-sm text-slate-400">{entrySentence}</p>
          </div>
          <button className="rounded border border-slate-700 px-3 py-1 text-sm text-slate-200 hover:bg-slate-800" onClick={onClose}>
            Close
          </button>
        </div>

        <section className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4">
            <p className="text-xs uppercase text-slate-500">Live metrics</p>
            <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
              {metrics.map((metric) => (
                <div key={metric.label}>
                  <dt className="text-[11px] uppercase text-slate-500">{metric.label}</dt>
                  <dd className="text-base text-white">{metric.value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4">
            <p className="text-xs uppercase text-slate-500">Mini chart</p>
            <MicroStructureChart tile={tile} bars={20} width={300} height={120} />
          </div>
        </section>

        <section className="mt-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase text-slate-500">Top 3 OTM</p>
            {!tile.options_top3.length && <span className="text-xs text-amber-300">Options warming…</span>}
          </div>
          <div className="mt-4 grid gap-3">
            {tile.options_top3.map((contract) => (
              <div key={contract.contract} className={clsx("rounded-xl border px-4 py-3 text-sm", contract.contract === selectedContract?.contract ? "border-emerald-500/60 bg-emerald-500/5" : "border-slate-800/80 bg-slate-900/40")}
                onClick={() => setSelectedContractId(contract.contract)}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-base text-white">{contract.contract}</p>
                    <p className="text-[12px] text-slate-400">{contract.expiry ?? "--"} · {contract.type?.toUpperCase() ?? "--"} · {contract.strike ?? "--"}</p>
                  </div>
                  <div className="text-right text-[12px] text-slate-400">
                    <p>Bid {contract.bid?.toFixed(2) ?? "--"} / Ask {contract.ask?.toFixed(2) ?? "--"}</p>
                    <p>Δ {contract.delta?.toFixed(2) ?? "--"} · OI {contract.oi ?? "--"}</p>
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-3">
                  <button className="rounded border border-emerald-400/60 px-3 py-1 text-xs text-emerald-200" onClick={() => handleLoad(contract)}>
                    Load Contract
                  </button>
                  <span className="text-[11px] text-slate-400">Spread {contract.spread_quality ?? "--"}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4">
          <p className="text-xs uppercase text-slate-500">Discord actions</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {(Object.keys(ACTION_LABELS) as Array<AlertPayload["action"]>).map((action) => (
              <button
                key={action}
                className={clsx(
                  "rounded-full px-4 py-1 text-sm",
                  activeAction === action ? "bg-emerald-500 text-emerald-950" : "bg-slate-800 text-slate-200 hover:bg-slate-700",
                )}
                onClick={() => setActiveAction((prev) => (prev === action ? null : action))}
              >
                {ACTION_LABELS[action]}
              </button>
            ))}
          </div>
          {activeAction && (
            <div className="mt-4 space-y-3">
              <textarea
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 p-3 text-sm text-white focus:border-emerald-500 focus:outline-none"
                rows={3}
                placeholder="Add color for Discord..."
                value={note}
                onChange={(event) => setNote(event.target.value)}
              />
              <div className="flex items-center gap-2 text-sm">
                <button
                  className="rounded-full bg-emerald-500 px-4 py-1.5 font-semibold text-emerald-950 disabled:opacity-50"
                  onClick={handleSend}
                  disabled={!canSend || sending}
                >
                  Send {ACTION_LABELS[activeAction]}
                </button>
                <button className="text-slate-400" onClick={() => setActiveAction(null)}>
                  Cancel
                </button>
                {!priceToSend && <span className="text-xs text-amber-300">Need live mid to send</span>}
              </div>
            </div>
          )}
        </section>

        <section className="mt-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs uppercase text-slate-500">Timeline</p>
            <p className="text-xs text-slate-400">Active trades: {trades.filter((trade) => trade.symbol === tile.symbol).length}</p>
          </div>
          {timeline.length ? (
            <ul className="mt-4 space-y-2 text-sm">
              {timeline.map((entry) => (
                <li key={entry.id} className="rounded-lg border border-slate-800/60 bg-slate-950/40 px-3 py-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white">{ACTION_LABELS[entry.action]}</span>
                    <span className="text-[11px] text-slate-500">{new Date(entry.createdAt).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    {entry.note || "No note"} · @{entry.price?.toFixed(2) ?? "--"} · Grade {entry.grade} · Conf {entry.confidence}%
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-500">No alerts sent yet.</p>
          )}
        </section>
      </aside>
    </div>
  );
}
