import { useEffect, useMemo, useRef, useState } from "react";
import { connectWS, getJSON, useTickers, type WsStatus } from "../api/client";

type LiveTile = Record<string, any> & { symbol: string; updatedAt: number };

type UseLiveTilesResult = {
  tiles: LiveTile[];
  lastHeartbeatAgo: number;
  status: WsStatus;
  now: number;
};

export function useLiveTiles(): UseLiveTilesResult {
  const { data } = useTickers();
  const tickers = data?.tickers ?? [];
  const tickerKey = tickers.join(",");
  const tilesRef = useRef<Map<string, LiveTile>>(new Map());
  const [version, setVersion] = useState(0);
  const [status, setStatus] = useState<WsStatus>("connecting");
  const [clock, setClock] = useState(Date.now());
  const heartbeatRef = useRef(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const map = tilesRef.current;

    for (const symbol of Array.from(map.keys())) {
      if (!tickers.includes(symbol)) {
        map.delete(symbol);
      }
    }

    const missing = tickers.filter((symbol) => !map.has(symbol));
    if (!missing.length) {
      setVersion((value) => value + 1);
      return () => {
        cancelled = true;
      };
    }

    (async () => {
      for (const symbol of missing) {
        try {
          const data = await getJSON<Record<string, any>>(`/api/tickers/${symbol}/state`);
          if (cancelled || !data?.symbol) continue;
          map.set(symbol, { ...(data as Record<string, any>), updatedAt: Date.now() } as LiveTile);
        } catch {
          // ignore individual fetch failures
        }
      }
      if (!cancelled) setVersion((value) => value + 1);
    })();

    return () => {
      cancelled = true;
    };
  }, [tickerKey]);

  useEffect(() => {
    const socket = connectWS((payload) => {
      if (payload?.type !== "tile" || typeof payload.data !== "object" || !payload.data) return;
      const tile = payload.data as Record<string, any>;
      if (!tile.symbol) return;
      const map = tilesRef.current;
      const previous = map.get(tile.symbol) || {};
      map.set(tile.symbol, { ...previous, ...tile, updatedAt: Date.now() } as LiveTile);
      heartbeatRef.current = Date.now();
      setVersion((value) => value + 1);
    }, setStatus);
    return () => socket.close();
  }, []);

  const tiles = useMemo(() => {
    const map = tilesRef.current;
    return tickers.map((symbol) => map.get(symbol)).filter((tile): tile is LiveTile => Boolean(tile));
  }, [tickerKey, version]);

  const lastHeartbeatAgo = Math.max(0, Math.round((clock - heartbeatRef.current) / 1000));

  return { tiles, lastHeartbeatAgo, status, now: clock };
}
