import { useState } from "react";
import { useWhatIf } from "../api/client";

function WhatIfPanel({ ticker }: { ticker: string }) {
  const mutation = useWhatIf();
  const [spread, setSpread] = useState(6);
  const [iv, setIv] = useState(-2);
  const [orb, setOrb] = useState(true);

  const run = () => {
    mutation.mutate({ ticker, deltas: { spreadShrinksTo: spread, ivChange: iv, orbRetestConfirms: orb } });
  };

  const result = mutation.data;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <h3 className="font-semibold">What-If</h3>
      <div className="mt-3 space-y-2 text-sm">
        <label className="block">
          Spread%
          <input type="number" className="mt-1 w-full rounded bg-slate-800 p-2" value={spread} onChange={(e) => setSpread(Number(e.target.value))} />
        </label>
        <label className="block">
          IV change
          <input type="number" className="mt-1 w-full rounded bg-slate-800 p-2" value={iv} onChange={(e) => setIv(Number(e.target.value))} />
        </label>
        <label className="flex items-center gap-2 text-xs">
          <input type="checkbox" checked={orb} onChange={(e) => setOrb(e.target.checked)} /> ORB retest confirms
        </label>
      </div>
      <button className="mt-4 w-full rounded bg-emerald-700 py-2 text-sm" onClick={run} disabled={mutation.isPending}>
        {mutation.isPending ? "Running..." : "Recompute"}
      </button>
      {result ? (
        <p className="mt-3 text-xs text-slate-300">
          Revised {Math.round(result.revisedProbToAction * 100)}% → {result.revisedBand}
        </p>
      ) : null}
    </div>
  );
}

export default WhatIfPanel;
