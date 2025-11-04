import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import * as api from "../../api/client";
import AdminLevers from "../../components/AdminLevers";

const mutate = vi.fn();
vi.spyOn(api, "usePolicyMutation").mockReturnValue({ mutate } as any);

it("sends policy mutation", () => {
  render(<AdminLevers />);
  fireEvent.click(screen.getByText(/Apply to all/));
  expect(mutate).toHaveBeenCalled();
});
