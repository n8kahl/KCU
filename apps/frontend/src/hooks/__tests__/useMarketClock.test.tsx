import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useMarketClock } from "../../hooks/useMarketClock";

describe("useMarketClock", () => {
  it("returns late session guidance after 15:00 ET", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2024-03-01T20:10:00Z"));
    const { result } = renderHook(() => useMarketClock());
    expect(result.current.session).toBe("Late");
    expect(result.current.warningAfterThree).toBe(true);
    vi.useRealTimers();
  });
});
