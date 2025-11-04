import { useEffect, useState } from "react";
import AdminLevers from "../components/AdminLevers";
import DetailDrawer from "../components/DetailDrawer";
import WhatIfPanel from "../components/WhatIfPanel";
import TickerTile from "../components/TickerTile";
import { connectWS, useTickers, useTile } from "../api/client";

function Dashboard() {
  const { data } = useTickers();
  const [selected, setSelected] = useState<string | undefined>();
  const tileQuery = useTile(selected || data?.tickers?.[0]);
  const [liveTile, setLiveTile] = useState<any | null>(null);
  const [drawerTile, setDrawerTile] = useState<any | null>(null);

  useEffect(() => {
    if (!selected && data?.tickers?.length) {
      setSelected(data.tickers[0]);
    }
  }, [data, selected]);

  const drawerSymbol = drawerTile?.symbol;

  useEffect(() => {
    const socket = connectWS((payload) => {
      if (payload?.type !== "tile" || !payload.data || typeof payload.data !== "object") {
        return;
      }
      const tilePayload = payload.data as { symbol?: string } & Record<string, unknown>;
      if (tilePayload.symbol === selected) {
        setLiveTile(tilePayload);
      }
      if (drawerSymbol && tilePayload.symbol === drawerSymbol) {
        setDrawerTile(tilePayload);
      }
    });
    return () => socket.close();
  }, [selected, drawerSymbol]);

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
        {tile ? (
          <TickerTile tile={tile} onAction={() => {}} onInspect={(payload) => setDrawerTile(payload)} />
        ) : (
          <div className="rounded border border-slate-800 p-6">Loading…</div>
        )}
      </section>
      <section className="space-y-4">
        {selected && <WhatIfPanel ticker={selected} />}
        <AdminLevers />
      </section>
      {drawerTile && <DetailDrawer tile={drawerTile} onClose={() => setDrawerTile(null)} />}
    </main>
  );
}

export default Dashboard;
