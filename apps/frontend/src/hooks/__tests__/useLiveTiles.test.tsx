import { describe, expect, it } from "vitest";
import { sortTilesByGradeConfidence } from "../../hooks/useLiveTiles";

describe("sortTilesByGradeConfidence", () => {
  it("orders tiles by grade then confidence", () => {
    const tiles = [
      { symbol: "AMD", grade: "B", confidence_score: 80 },
      { symbol: "MSFT", grade: "A", confidence_score: 60 },
      { symbol: "AAPL", grade: "A", confidence_score: 92 },
      { symbol: "TSLA", grade: "C", confidence_score: 90 },
    ];
    const sorted = sortTilesByGradeConfidence(tiles);
    expect(sorted.map((tile) => tile.symbol)).toEqual(["AAPL", "MSFT", "AMD", "TSLA"]);
  });
});
