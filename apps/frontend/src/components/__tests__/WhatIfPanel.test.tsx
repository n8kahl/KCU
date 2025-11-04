import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import * as api from "../../api/client";
import WhatIfPanel from "../../components/WhatIfPanel";

vi.spyOn(api, "useWhatIf").mockReturnValue({ mutate: vi.fn(), data: null } as any);

test("submits payload", () => {
  const panel = render(<WhatIfPanel ticker="SPY" />);
  fireEvent.click(panel.getByText(/Recompute/i));
  expect(api.useWhatIf).toHaveBeenCalled();
});
