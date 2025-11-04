import { useState } from "react";
import { usePolicyMutation } from "../api/client";

const MODES = ["Conservative", "Standard", "Aggressive"];

function AdminLevers() {
  const [mode, setMode] = useState("Standard");
  const [overrides, setOverrides] = useState({ patience: 0, orb: 0, spread: 0, breadth: 0 });
  const mutation = usePolicyMutation();

  const submit = () => {
    mutation.mutate({ mode, overrides: overrides as any });
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="flex justify-between">
        <h3 className="font-semibold">Admin Levers</h3>
        <select className="rounded bg-slate-800 p-2" value={mode} onChange={(e) => setMode(e.target.value)}>
          {MODES.map((m) => (
            <option key={m}>{m}</option>
          ))}
        </select>
      </div>
      {Object.entries(overrides).map(([key, value]) => (
        <label key={key} className="mt-3 block text-xs uppercase text-slate-400">
          {key}
          <input
            type="range"
            min={-10}
            max={10}
            value={value}
            onChange={(e) => setOverrides((prev) => ({ ...prev, [key]: Number(e.target.value) }))}
            className="mt-1 w-full"
          />
        </label>
      ))}
      <button className="mt-4 w-full rounded bg-brand-700 py-2 text-sm" onClick={submit}>
        Apply to all
      </button>
    </div>
  );
}

export default AdminLevers;
