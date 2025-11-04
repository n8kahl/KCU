import { render, screen } from "@testing-library/react";
import TickerTile from "../../components/TickerTile";

const mockTile = {
  symbol: "SPY",
  regime: "Normal",
  probability_to_action: 0.82,
  band: { label: "EntryReady" },
  confidence: { p50: 0.7 },
  rationale: { positives: ["Trend"], risks: ["Event"] },
  options: { spread_pct: 5, ivr: 30, delta_target: 0.4 },
};

test("renders key fields", () => {
  render(<TickerTile tile={mockTile} onAction={() => {}} />);
  expect(screen.getByText("SPY")).toBeInTheDocument();
  expect(screen.getByText("82%")).toBeInTheDocument();
});
