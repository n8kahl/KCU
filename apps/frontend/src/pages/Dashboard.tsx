import { useState } from "react";
import ActiveTrades from "../components/ActiveTrades";
import DetailDrawer from "../components/DetailDrawer";
import MarketHeader from "../components/MarketHeader";
import TickerCard from "../components/TickerCard";
import WatchlistManager from "../components/WatchlistManager";
import { useLiveTiles } from "../hooks/useLiveTiles";
import type { Tile } from "../types";

function Dashboard() {
  const { tiles, lastHeartbeatAgo, status, now } = useLiveTiles();
  const [selectedTile, setSelectedTile] = useState<Tile | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 text-slate-100">
      <MarketHeader status={status} lastHeartbeatAgo={lastHeartbeatAgo}>
        <WatchlistManager />
      </MarketHeader>

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
