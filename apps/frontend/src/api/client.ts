import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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

type WsPayload = { type?: string; data?: unknown };

function connectWS(onMessage: (payload: WsPayload) => void) {
  const wsUrl = BACKEND.replace(/^http/, "ws") + "/ws/stream";
  const socket = new WebSocket(wsUrl);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}

function useTickers() {
  return useQuery<{ tickers: string[] }>({ queryKey: ["tickers"], queryFn: () => getJSON("/api/tickers") });
}

function useTile(symbol: string | undefined) {
  return useQuery<{ symbol: string } & Record<string, unknown>>({
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
    mutationFn: (payload) =>
      postJSON("/api/admin/policy", payload, { headers: { "x-api-key": localStorage.getItem("kcu_api_key") || "" } }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["tile"] }),
  });
}

export type { WhatIfResponse };
export { BACKEND, connectWS, getJSON, postJSON, usePolicyMutation, useTickers, useTile, useWhatIf };
