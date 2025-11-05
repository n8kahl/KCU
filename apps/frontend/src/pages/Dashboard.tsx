import ActiveTrades from "../components/ActiveTrades";
import TickerCard from "../components/TickerCard";
import WatchlistManager from "../components/WatchlistManager";
import { useLiveTiles } from "../hooks/useLiveTiles";
import type { WsStatus } from "../api/client";

function Dashboard() {
  const { tiles, lastHeartbeatAgo, status, now } = useLiveTiles();

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
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
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
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 lg:flex-row">
        <section className="flex-1">
          {tiles.length ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {tiles.map((tile) => (
                <TickerCard key={tile.symbol} tile={tile} now={now} />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-10 text-center text-slate-400">No tiles available.</div>
          )}
        </section>
        <div className="w-full lg:w-[360px] xl:w-[420px]">
          <ActiveTrades />
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
