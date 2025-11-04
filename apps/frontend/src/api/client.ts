import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const BACKEND = import.meta.env.VITE_BACKEND_URL || "http://localhost:3001";

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

function connectWS(onMessage: (payload: any) => void) {
  const wsUrl = BACKEND.replace(/^http/, "ws") + "/ws/stream";
  const socket = new WebSocket(wsUrl);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}

function useTickers() {
  return useQuery<{ tickers: string[] }>({ queryKey: ["tickers"], queryFn: () => getJSON("/api/tickers") });
}

function useTile(symbol: string | undefined) {
  return useQuery<{ symbol: string } & Record<string, any>>({
    queryKey: ["tile", symbol],
    queryFn: () => getJSON(`/api/tickers/${symbol}/state`),
    enabled: Boolean(symbol),
    refetchInterval: 15000,
  });
}

function useWhatIf() {
  return useMutation({
    mutationFn: (payload: { ticker: string; deltas: Record<string, number | boolean> }) =>
      postJSON("/api/what-if", payload),
  });
}

function usePolicyMutation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: { mode: string; overrides: Record<string, number> }) =>
      postJSON("/api/admin/policy", payload, { headers: { "x-api-key": localStorage.getItem("kcu_api_key") || "" } }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["tile"] }),
  });
}

export { BACKEND, connectWS, getJSON, postJSON, usePolicyMutation, useTickers, useTile, useWhatIf };
