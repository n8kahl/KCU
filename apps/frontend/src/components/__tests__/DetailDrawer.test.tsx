import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DetailDrawer from "../DetailDrawer";
import type { Tile } from "../../types";
import { useTrades } from "../../store/trades";

vi.mock("../../api/client", () => ({
  postAlert: vi.fn().mockResolvedValue({ status: "ok" }),
}));

const baseTile: Tile = {
  symbol: "SPY",
  regime: "Momentum",
  grade: "A",
  confidence_score: 95,
  confidence: {},
  probability_to_action: 0.92,
  band: { label: "EntryReady" },
  breakdown: [{ name: "TrendStack", score: 0.82 }],
  options: {},
  options_top3: [
    {
      contract: "O:SPY240621C00450000",
      ticker: "SPY",
      expiry: "2024-06-21",
      strike: 450,
      type: "call",
      bid: 2.4,
      ask: 2.6,
      mid: 2.5,
      delta: 0.45,
      oi: 1200,
      spread_quality: "tight",
    },
  ],
  rationale: { positives: ["Stacked trend"] },
  admin: {
    lastPrice: 450,
    managing: {
      entry: 450,
      direction: "long",
      tp1: { price: 455, label: "TP1" },
      tp2: { price: 458, label: "TP2" },
      runner: { trail: 446 },
    },
    marketMicro: { microChop: 0.2 },
    orb: { range_pct: 0.1 },
    timing: { label: "Open" },
    atr: 2,
  },
  timestamps: { updated: new Date().toISOString() },
  penalties: {},
  bonuses: {},
  history: [],
  delta_to_entry: { dollars: 0.5, percent: 0.11, at_entry: true, direction: "above" },
  key_level_label: "ORB High",
  bars: [{ o: 450, h: 451, l: 449, c: 450, v: 1000, t: new Date().toISOString() }],
  ema8: [450],
  ema21: [449.8],
  vwap: [450.1],
  key_levels: [{ label: "ORB High", price: 451 }],
  patience_candle: true,
};

function buildTile(): Tile {
  return JSON.parse(JSON.stringify(baseTile));
}

beforeEach(() => {
  useTrades.getState().clear();
  localStorage.clear();
});

describe("DetailDrawer", () => {
  it("renders plain-English plan", () => {
    render(<DetailDrawer tile={buildTile()} onClose={() => {}} />);
    expect(screen.getByText(/SPY A setup/i)).toBeInTheDocument();
  });

  it("loads contract into active trades", () => {
    render(<DetailDrawer tile={buildTile()} onClose={() => {}} />);
    fireEvent.click(screen.getAllByText(/Load Contract/i)[0]);
    expect(useTrades.getState().trades).toHaveLength(1);
  });

  it("sends alert and updates timeline", async () => {
    render(<DetailDrawer tile={buildTile()} onClose={() => {}} />);
    fireEvent.click(screen.getAllByText(/Load Contract/i)[0]);
    fireEvent.click(screen.getAllByText("Enter")[0]);
    const textarea = screen.getByPlaceholderText(/Add color/i);
    fireEvent.change(textarea, { target: { value: "Go time" } });
    fireEvent.click(screen.getByText(/Send Enter/i));
    await waitFor(() => expect(screen.getByText(/Go time/)).toBeInTheDocument());
  });
});
