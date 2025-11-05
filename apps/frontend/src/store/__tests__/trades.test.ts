import { beforeEach, describe, expect, it } from "vitest";
import { useTrades } from "../trades";
import type { AlertPayload } from "../../types";

const contract = {
  contract: "O:SPY240621C00450000",
  ticker: "SPY",
  expiry: "2024-06-21",
  strike: 450,
  type: "call",
  bid: 2.4,
  ask: 2.6,
  mid: 2.5,
  delta: 0.45,
  oi: 1000,
  spread_quality: "tight",
};

beforeEach(() => {
  useTrades.getState().clear();
  localStorage.clear();
});

describe("trade store", () => {
  it("updates PnL from live mid prices", () => {
    useTrades.getState().loadContract("SPY", contract as any);
    const payload: AlertPayload = {
      action: "enter",
      symbol: "SPY",
      contract: contract.contract,
      price: 2,
      grade: "A",
      confidence: 90,
      level: "ORB High",
      stop: 1,
      target: 3,
    };
    useTrades.getState().recordAlert(contract.contract, payload);
    useTrades.getState().syncTile({ symbol: "SPY", options_top3: [{ ...contract, mid: 2.5 }] } as any);
    const trade = useTrades.getState().trades[0];
    expect(trade.pnlPct).toBeCloseTo(25);
  });
});
