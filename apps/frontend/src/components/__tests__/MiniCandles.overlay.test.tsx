import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MiniCandles from "../MiniCandles";

describe("MiniCandles overlays", () => {
  it("draws overlays and moving averages", () => {
    const closes = Array.from({ length: 50 }, (_, idx) => 100 + idx * 0.1);
    const { container } = render(
      <MiniCandles
        closes={closes}
        levels={[
          { label: "HOD", price: 104 },
          { label: "VWAP", price: 102 },
        ]}
        managing={{
          entry: 101.2,
          targets: [
            { label: "TP1", price: 102.5 },
            { label: "TP2", price: 103.5 },
          ],
          runner: { trail: 100.8 },
        }}
        aPlusEntry
      />,
    );
    expect(container.querySelectorAll("polyline").length).toBeGreaterThanOrEqual(3);
    expect(container.querySelectorAll("line").length).toBeGreaterThan(6);
  });
});
