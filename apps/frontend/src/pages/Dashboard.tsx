import { useEffect, useState } from "react";
import AdminLevers from "../components/AdminLevers";
import DetailDrawer from "../components/DetailDrawer";
import TickerCarousel from "../components/TickerCarousel";
import WhatIfPanel from "../components/WhatIfPanel";
import TickerTile from "../components/TickerTile";
import { connectWS, useTickers, useTile, type WsStatus } from "../api/client";
import useSwipeNavigation from "../hooks/useSwipeNavigation";

function Dashboard() {
  const { data } = useTickers();
  const [selected, setSelected] = useState<string | undefined>();
  const tickerList = data?.tickers || [];
  const tileQuery = useTile(selected || tickerList[0]);
  const [liveTile, setLiveTile] = useState<any | null>(null);
  const [drawerTile, setDrawerTile] = useState<any | null>(null);
  const [streamStatus, setStreamStatus] = useState<WsStatus>("connecting");
  const currentIndex = selected ? tickerList.indexOf(selected) : 0;

  const cycleSymbol = (direction: number) => {
    if (!tickerList.length) return;
    const baseIndex = currentIndex >= 0 ? currentIndex : 0;
    const nextIndex = (baseIndex + direction + tickerList.length) % tickerList.length;
    setSelected(tickerList[nextIndex]);
  };

  const swipeHandlers = useSwipeNavigation({ onSwipeLeft: () => cycleSymbol(1), onSwipeRight: () => cycleSymbol(-1) });

  useEffect(() => {
    if (!selected && data?.tickers?.length) {
      setSelected(data.tickers[0]);
    }
  }, [data, selected]);

  const drawerSymbol = drawerTile?.symbol;

  useEffect(() => {
    setStreamStatus("connecting");
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
    }, setStreamStatus);
    return () => socket.close();
  }, [selected, drawerSymbol]);

  const tile = liveTile || tileQuery.data;

  const statusLabel =
    streamStatus === "online" ? "Live" : streamStatus === "connecting" ? "Connecting…" : "Offline";
  const statusTone =
    streamStatus === "online" ? "bg-emerald-500/20 text-emerald-200 border-emerald-400/40" : streamStatus === "connecting" ? "bg-amber-500/10 text-amber-200 border-amber-400/30" : "bg-rose-500/10 text-rose-200 border-rose-400/30";

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 p-4 sm:p-6">
      <section className="space-y-4">
        <header className="glass-panel rounded-3xl p-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Watchlist</p>
              <h1 className="text-3xl font-semibold text-white">KCU LTP Admin Copilot</h1>
              <p className="text-sm text-slate-400">Swipe or tap symbols to jump between tiles.</p>
            </div>
            <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${statusTone}`}>
              <span className="h-2 w-2 rounded-full bg-current" />
              {statusLabel}
            </div>
          </div>
          <div className="mt-4">
            <TickerCarousel tickers={tickerList} selected={selected} onSelect={(symbol) => setSelected(symbol)} />
          </div>
        </header>
        {tile ? (
          <TickerTile tile={tile} onAction={() => {}} onInspect={(payload) => setDrawerTile(payload)} swipeHandlers={swipeHandlers} />
        ) : (
          <div className="glass-panel rounded-2xl p-10 text-center text-slate-400">Loading tile…</div>
        )}
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        {selected && <WhatIfPanel ticker={selected} />}
        <AdminLevers />
      </section>
      {drawerTile && <DetailDrawer tile={drawerTile} onClose={() => setDrawerTile(null)} />}
    </main>
  );
}

export default Dashboard;
