import { useEffect, useMemo, useState } from "react";
import AdminLevers from "../components/AdminLevers";
import WhatIfPanel from "../components/WhatIfPanel";
import TickerTile from "../components/TickerTile";
import { connectWS, useTickers, useTile } from "../api/client";

function Dashboard() {
  const { data } = useTickers();
  const [selected, setSelected] = useState<string | undefined>();
  const tileQuery = useTile(selected || data?.tickers?.[0]);
  const [liveTile, setLiveTile] = useState<any | null>(null);

  useEffect(() => {
    if (!selected && data?.tickers?.length) {
      setSelected(data.tickers[0]);
    }
  }, [data, selected]);

  useEffect(() => {
    const socket = connectWS((payload) => {
      if (payload.type === "tile" && payload.data.symbol === selected) {
        setLiveTile(payload.data);
      }
    });
    return () => socket.close();
  }, [selected]);

  const tile = liveTile || tileQuery.data;

  return (
    <main className="mx-auto grid max-w-6xl gap-6 p-6 md:grid-cols-[2fr_1fr]">
      <section>
        <div className="mb-4 flex flex-wrap gap-2">
          {data?.tickers?.map((symbol) => (
            <button
              key={symbol}
              className={`rounded-full border px-3 py-1 text-sm ${selected === symbol ? "border-emerald-500" : "border-slate-700"}`}
              onClick={() => setSelected(symbol)}
            >
              {symbol}
            </button>
          ))}
        </div>
        {tile ? <TickerTile tile={tile} onAction={() => {}} /> : <div className="rounded border border-slate-800 p-6">Loading…</div>}
      </section>
      <section className="space-y-4">
        {selected && <WhatIfPanel ticker={selected} />}
        <AdminLevers />
      </section>
    </main>
  );
}

export default Dashboard;
