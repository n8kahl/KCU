import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ActiveTrade, AlertPayload, Contract, Tile } from "../types";

type TradeStore = {
  trades: ActiveTrade[];
  loadContract: (symbol: string, contract: Contract) => void;
  remove: (contractId: string) => void;
  clear: () => void;
  recordAlert: (contractId: string, payload: AlertPayload) => void;
  close: (contractId: string) => void;
  syncTile: (tile: Tile) => void;
  reAlertTemplate: (contractId: string) => AlertPayload | null;
};

const UPDATE_LIMIT = 12;

export const useTrades = create<TradeStore>()(
  persist(
    (set, get) => ({
      trades: [],
      loadContract: (symbol, contract) =>
        set((state) => {
          const existing = state.trades.find((trade) => trade.contractId === contract.contract);
          const entry: ActiveTrade = existing
            ? { ...existing, contract }
            : {
                contractId: contract.contract,
                symbol,
                contract,
                timeline: [],
                isClosed: false,
              };
          const next = [entry, ...state.trades.filter((trade) => trade.contractId !== contract.contract)].slice(0, UPDATE_LIMIT);
          return { ...state, trades: next };
        }),
      remove: (contractId) =>
        set((state) => ({
          ...state,
          trades: state.trades.filter((trade) => trade.contractId !== contractId),
        })),
      clear: () => ({ trades: [] }),
      recordAlert: (contractId, payload) =>
        set((state) => {
          const updated = state.trades.map((trade) => {
            if (trade.contractId !== contractId) return trade;
            const alert = {
              id: `${payload.action}-${Date.now()}`,
              action: payload.action,
              note: payload.note,
              price: payload.price,
              grade: payload.grade,
              confidence: payload.confidence,
              level: payload.level,
              stop: payload.stop,
              target: payload.target,
              createdAt: Date.now(),
            };
            const entryPrice = payload.action === "enter" && payload.price ? payload.price : trade.entryPrice;
            const pnlPct =
              typeof entryPrice === "number" && typeof trade.latestMid === "number"
                ? ((trade.latestMid - entryPrice) / entryPrice) * 100
                : trade.pnlPct;
            return {
              ...trade,
              entryPrice,
              pnlPct,
              lastTemplate: payload,
              timeline: [...trade.timeline, alert],
            };
          });
          return { ...state, trades: updated };
        }),
      close: (contractId) =>
        set((state) => ({
          ...state,
          trades: state.trades.map((trade) => {
            if (trade.contractId !== contractId) return trade;
            return { ...trade, isClosed: true, closedAt: Date.now() };
          }),
        })),
      syncTile: (tile) =>
        set((state) => {
          if (!tile.options_top3?.length) return state;
          const updated = state.trades.map((trade) => {
            if (trade.symbol !== tile.symbol) return trade;
            const live = tile.options_top3.find((option) => option.contract === trade.contractId);
            if (!live) return trade;
            const latestMid = live.mid ?? live.bid ?? live.ask ?? trade.latestMid;
            const entryPrice = trade.entryPrice;
            const pnlPct =
              entryPrice && typeof latestMid === "number" ? ((latestMid - entryPrice) / entryPrice) * 100 : trade.pnlPct;
            return {
              ...trade,
              contract: { ...trade.contract, ...live },
              latestMid: latestMid ?? trade.latestMid,
              pnlPct,
            };
          });
          return { ...state, trades: updated };
        }),
      reAlertTemplate: (contractId) => get().trades.find((item) => item.contractId === contractId)?.lastTemplate ?? null,
    }),
    {
      name: "kcu-active-trades",
      partialize: (state) => ({ trades: state.trades }),
    },
  ),
);

export const tradesStore = useTrades;
