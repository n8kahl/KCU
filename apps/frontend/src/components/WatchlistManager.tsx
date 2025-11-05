import { FormEvent, useState } from "react";
import { useAddTicker, useRemoveTicker, useTickers } from "../api/client";

function WatchlistManager() {
  const { data, isLoading } = useTickers();
  const addMutation = useAddTicker();
  const removeMutation = useRemoveTicker();
  const [symbolInput, setSymbolInput] = useState("");
  const tickers = data?.tickers || [];

  const handleAdd = (event: FormEvent) => {
    event.preventDefault();
    const cleaned = symbolInput.trim().toUpperCase();
    if (!cleaned || addMutation.isPending) return;
    addMutation.mutate({ ticker: cleaned });
    setSymbolInput("");
  };

  const handleRemove = (symbol: string) => {
    if (removeMutation.isPending) return;
    removeMutation.mutate({ ticker: symbol });
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {isLoading && <span className="text-xs text-slate-500">Loading…</span>}
      {tickers.map((ticker) => (
        <button
          key={ticker}
          onClick={() => handleRemove(ticker)}
          className="group inline-flex items-center gap-2 rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-200 transition hover:border-rose-600 hover:text-rose-200"
        >
          {ticker}
          <span className="text-slate-500 transition group-hover:text-rose-200">×</span>
        </button>
      ))}
      <form onSubmit={handleAdd} className="inline-flex items-center gap-2">
        <input
          className="w-24 rounded-full border border-slate-700 bg-slate-900/60 px-3 py-1 text-xs uppercase text-slate-200 outline-none focus:border-emerald-500"
          placeholder="Add"
          value={symbolInput}
          onChange={(event) => setSymbolInput(event.target.value.toUpperCase())}
        />
      </form>
    </div>
  );
}

export default WatchlistManager;
