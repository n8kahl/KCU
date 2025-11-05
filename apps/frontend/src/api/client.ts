import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AlertPayload, Tile } from "../types";

const FALLBACK_BACKEND =
  typeof window !== "undefined" && window.location.hostname.endsWith("railway.app")
    ? "https://kcu.up.railway.app"
    : "http://localhost:3001";
const BACKEND = import.meta.env.VITE_BACKEND_URL || FALLBACK_BACKEND;

type WhatIfPayload = { ticker: string; deltas: Record<string, number | boolean> };
type WhatIfResponse = {
  symbol: string;
  revisedProbToAction: number;
  revisedBand: string;
  revisedETAsec?: number | null;
};

async function getJSON<T>(path: string): Promise<T> {
  const resp = await fetch(`${BACKEND}${path}`);
  if (!resp.ok) throw new Error(`Request failed ${resp.status}`);
  return resp.json();
}

async function postJSON<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BACKEND}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    body: JSON.stringify(body),
    ...init,
  });
  if (!resp.ok) throw new Error(`Request failed ${resp.status}`);
  return resp.json();
}

async function deleteJSON(path: string): Promise<void> {
  const resp = await fetch(`${BACKEND}${path}`, { method: "DELETE" });
  if (!resp.ok) throw new Error(`Request failed ${resp.status}`);
}

type WsPayload = { type?: string; data?: unknown };
type WsStatus = "connecting" | "online" | "offline";

function connectWS(onMessage: (payload: WsPayload) => void, onStatus?: (status: WsStatus) => void) {
  const wsUrl = BACKEND.replace(/^http/, "ws") + "/ws/stream";
  const socket = new WebSocket(wsUrl);
  onStatus?.("connecting");
  socket.onopen = () => onStatus?.("online");
  socket.onclose = () => onStatus?.("offline");
  socket.onerror = () => onStatus?.("offline");
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}

function useTickers() {
  return useQuery<{ tickers: string[] }>({ queryKey: ["tickers"], queryFn: () => getJSON("/api/tickers") });
}

function useTile(symbol: string | undefined) {
  return useQuery<Tile>({
    queryKey: ["tile", symbol],
    queryFn: () => getJSON(`/api/tickers/${symbol}/state`),
    enabled: Boolean(symbol),
    refetchInterval: 15000,
  });
}

function useWhatIf() {
  return useMutation<WhatIfResponse, Error, WhatIfPayload>({
    mutationFn: (payload) => postJSON("/api/what-if", payload),
  });
}

function usePolicyMutation() {
  const client = useQueryClient();
  return useMutation<{ message: string }, Error, { mode: string; overrides: Record<string, number> }>({
    mutationFn: (payload) => postJSON("/api/admin/policy", payload),
    onSuccess: () => client.invalidateQueries({ queryKey: ["tile"] }),
  });
}

function useAddTicker() {
  const client = useQueryClient();
  return useMutation<void, Error, { ticker: string }>({
    mutationFn: ({ ticker }) => postJSON("/api/tickers", { ticker: ticker.trim().toUpperCase() }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["tickers"] });
      client.invalidateQueries({ queryKey: ["tile"] });
    },
  });
}

function useRemoveTicker() {
  const client = useQueryClient();
  return useMutation<void, Error, { ticker: string }>({
    mutationFn: ({ ticker }) => deleteJSON(`/api/tickers/${ticker}`),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["tickers"] });
      client.invalidateQueries({ queryKey: ["tile"] });
    },
  });
}

export type { WhatIfResponse, WsStatus };
async function postAlert(payload: AlertPayload): Promise<{ status: string }> {
  return postJSON("/api/alerts", payload);
}

export {
  BACKEND,
  connectWS,
  getJSON,
  postJSON,
  postAlert,
  usePolicyMutation,
  useTickers,
  useTile,
  useWhatIf,
  useAddTicker,
  useRemoveTicker,
};
