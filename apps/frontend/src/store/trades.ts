import { create } from "zustand";

export type LoadedContract = {
  ticker: string;
  contractId: string;
  label: string;
  mid?: number;
  delta?: number;
  dte?: number;
  spreadPct?: number;
};

type TradeState = {
  loaded: LoadedContract[];
  add: (contract: LoadedContract) => void;
  remove: (contractId: string) => void;
  clear: () => void;
};

export const useTrades = create<TradeState>((set) => ({
  loaded: [],
  add: (contract) =>
    set((state) => {
      const filtered = state.loaded.filter((item) => item.contractId !== contract.contractId);
      return { loaded: [contract, ...filtered].slice(0, 20) };
    }),
  remove: (contractId) => set((state) => ({ loaded: state.loaded.filter((item) => item.contractId !== contractId) })),
  clear: () => set({ loaded: [] }),
}));
