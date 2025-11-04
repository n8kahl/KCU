import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import TickerTile from "../../components/TickerTile";

const mockTile = {
  symbol: "SPY",
  regime: "Normal",
  probability_to_action: 0.82,
  band: { label: "EntryReady" },
  confidence: { p95: 0.88 },
  history: [{ score: 70 }, { score: 75 }],
  rationale: { positives: ["Trend"], risks: ["Event"] },
  breakdown: [
    { name: "TrendStack", score: 0.8 },
    { name: "Levels", score: 0.7 },
  ],
  options: {
    spread_pct: 5,
    spread_percentile_label: "p60",
    flicker_per_sec: 2,
    nbbo: "stable",
    liquidity_risk: 55,
    contracts: { primary: "O:SPXPRIMARY", backups: ["O:SPXALT"] },
  },
  admin: { marketMicro: { minuteThrust: 0.5 }, timing: { label: "10:00 ET", tf_primary: "5m" }, lastPrice: 444.2 },
};

test("renders key fields and detail button", () => {
  render(<TickerTile tile={mockTile} onAction={() => {}} onInspect={() => {}} />);
  expect(screen.getByText("SPY")).toBeInTheDocument();
  expect(screen.getByText("82%")).toBeInTheDocument();
  expect(screen.getByText("Spread")).toBeInTheDocument();
  expect(screen.getByText(/View details/i)).toBeInTheDocument();
});
