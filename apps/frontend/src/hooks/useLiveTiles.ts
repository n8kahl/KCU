import { useEffect, useMemo, useRef, useState } from "react";
import { connectWS, getJSON, useTickers, type WsStatus } from "../api/client";
import type { Tile } from "../types";
import { tradesStore } from "../store/trades";

type LiveTile = Tile & { updatedAt: number };

type UseLiveTilesResult = {
  tiles: LiveTile[];
  lastHeartbeatAgo: number;
  status: WsStatus;
  now: number;
};

const GRADE_ORDER: Record<string, number> = {
  "A+": 10,
  A: 9,
  "A-": 8,
  "B+": 7,
  B: 6,
  "B-": 5,
  "C+": 4,
  C: 3,
  "C-": 2,
  D: 1,
  F: 0,
};

function gradeValue(grade: string | undefined) {
  if (!grade) return 0;
  return GRADE_ORDER[grade] ?? 0;
}

export function sortTilesByGradeConfidence<T extends { grade?: string; confidence_score?: number; symbol: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const gradeDiff = gradeValue(b.grade) - gradeValue(a.grade);
    if (gradeDiff !== 0) return gradeDiff;
    return (b.confidence_score ?? 0) - (a.confidence_score ?? 0);
  });
}

function mergeTile(existing: LiveTile | undefined, incoming: Tile): LiveTile {
  if (!existing) {
    return { ...incoming, updatedAt: Date.now() };
  }
  Object.assign(existing, incoming, { updatedAt: Date.now() });
  return existing;
}

export function useLiveTiles(): UseLiveTilesResult {
  const { data } = useTickers();
  const tickers = data?.tickers ?? [];
  const tickerKey = tickers.join(",");
  const tilesRef = useRef<Map<string, LiveTile>>(new Map());
  const orderRef = useRef<string[]>([]);
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
          const data = await getJSON<Tile>(`/api/tickers/${symbol}/state`);
          if (cancelled || !data?.symbol) continue;
          map.set(symbol, { ...data, updatedAt: Date.now() });
          tradesStore.getState().syncTile(data);
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
      if (payload?.type === "heartbeat") {
        heartbeatRef.current = Date.now();
        return;
      }
      if (payload?.type !== "tile" || typeof payload.data !== "object" || !payload.data) return;
      const tile = payload.data as Tile;
      if (!tile.symbol) return;
      const map = tilesRef.current;
      const merged = mergeTile(map.get(tile.symbol), tile);
      map.set(tile.symbol, merged);
      tradesStore.getState().syncTile(merged);
      heartbeatRef.current = Date.now();
      setVersion((value) => value + 1);
    }, setStatus);
    return () => socket.close();
  }, []);

  const tiles = useMemo(() => {
    const map = tilesRef.current;
    const available = tickers.map((symbol) => map.get(symbol)).filter((tile): tile is LiveTile => Boolean(tile));
    const sorted = sortTilesByGradeConfidence(available);
    const nextOrder = sorted.map((tile) => tile.symbol);
    const prevOrder = orderRef.current;
    const unchanged = prevOrder.length === nextOrder.length && prevOrder.every((symbol, idx) => symbol === nextOrder[idx]);
    const orderToUse = unchanged ? prevOrder : nextOrder;
    if (!unchanged) {
      orderRef.current = nextOrder;
    }
    return orderToUse.map((symbol) => map.get(symbol)).filter((tile): tile is LiveTile => Boolean(tile));
  }, [tickerKey, version]);

  const lastHeartbeatAgo = Math.max(0, Math.round((clock - heartbeatRef.current) / 1000));

  return { tiles, lastHeartbeatAgo, status, now: clock };
}
