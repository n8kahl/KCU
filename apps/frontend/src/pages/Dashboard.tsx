import { useState } from "react";
import ActiveTrades from "../components/ActiveTrades";
import DetailDrawer from "../components/DetailDrawer";
import TickerCard from "../components/TickerCard";
import WatchlistManager from "../components/WatchlistManager";
import type { WsStatus } from "../api/client";
import { useMarketClock } from "../hooks/useMarketClock";
import { useLiveTiles } from "../hooks/useLiveTiles";
import type { Tile } from "../types";

function Dashboard() {
  const { tiles, lastHeartbeatAgo, status, now } = useLiveTiles();
  const { etTime, session, guidelineText, warningAfterThree } = useMarketClock();
  const [selectedTile, setSelectedTile] = useState<Tile | null>(null);

  const statusLabel: Record<WsStatus, string> = {
    online: "Live",
    connecting: "Connecting…",
    offline: "Offline",
  };

  const toneMap: Record<WsStatus, string> = {
    online: "bg-emerald-500/20 text-emerald-200 border-emerald-400/40",
    connecting: "bg-amber-500/10 text-amber-200 border-amber-400/30",
    offline: "bg-rose-500/10 text-rose-200 border-rose-400/30",
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 text-slate-100">
      <header className="sticky top-0 z-10 border-b border-slate-900/80 bg-slate-950/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">KCU LTP</p>
              <h1 className="text-2xl font-semibold text-white">Admin Copilot</h1>
              <div className={`mt-2 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${toneMap[status]}`}>
                <span className="h-2 w-2 rounded-full bg-current" />
                {statusLabel[status]} · {lastHeartbeatAgo}s
              </div>
            </div>
            <WatchlistManager />
          </div>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap gap-3">
              <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 px-4 py-2">
                <p className="text-[11px] uppercase text-slate-500">Market Clock</p>
                <p className="text-lg font-semibold text-white">{etTime} ET</p>
              </div>
              <div className="rounded-2xl border border-slate-800/80 bg-slate-900/50 px-4 py-2 max-w-lg">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-white">{session}</p>
                  {warningAfterThree && <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[11px] text-amber-200">After 15:00 – caution</span>}
                </div>
                <p className="text-sm text-slate-300">{guidelineText}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 lg:flex-row">
        <section className="flex-1">
          {tiles.length ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {tiles.map((tile) => (
                <TickerCard key={tile.symbol} tile={tile} now={now} onExpand={setSelectedTile} />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-10 text-center text-slate-400">No tiles available.</div>
          )}
        </section>
        <div className="w-full lg:w-[380px] xl:w-[420px]">
          <ActiveTrades />
        </div>
      </main>
      {selectedTile && <DetailDrawer tile={selectedTile} onClose={() => setSelectedTile(null)} />}
    </div>
  );
}

export default Dashboard;
