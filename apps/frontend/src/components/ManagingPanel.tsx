import clsx from "clsx";

type ManagingPlan = {
  symbol: string;
  direction: string;
  entry: number;
  tp1: { price: number; label: string; distance_pct: number; hit?: boolean };
  tp2: { price: number; label: string; distance_pct: number; hit?: boolean };
  runner: { trail: number; extended_to?: number | null; continuation_prob?: number; reasons?: string[] };
  timing?: { label?: string };
  reasons?: string[];
};

type Props = {
  plan?: ManagingPlan | null;
};

function ManagingPanel({ plan }: Props) {
  if (!plan) return null;
  const levels = [plan.tp1, plan.tp2];
  return (
    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Managing</span>
        <span>{plan.timing?.label}</span>
      </div>
      <div className="mt-3 space-y-2">
        {levels.map((lvl) => (
          <div key={lvl.label} className="flex items-center justify-between text-sm">
            <div>
              <p className="text-slate-300">{lvl.label}</p>
              <p className="text-xs text-slate-500">{lvl.distance_pct}% from entry</p>
            </div>
            <span className={clsx("rounded px-2 py-1 text-xs", lvl.hit ? "bg-emerald-800 text-emerald-100" : "bg-slate-800 text-slate-200")}>${lvl.price.toFixed(2)}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-lg bg-slate-950/60 p-3 text-sm">
        <p className="text-slate-300">Runner trail @ ${plan.runner.trail.toFixed(2)}</p>
        {plan.runner.extended_to && <p className="text-xs text-slate-400">Extended to ${plan.runner.extended_to.toFixed(2)}</p>}
        <p className="text-xs text-slate-400">Continuation {Math.round((plan.runner.continuation_prob ?? 0) * 100)}%</p>
        <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-slate-300">
          {(plan.runner.reasons || plan.reasons || []).map((reason) => (
            <span key={reason} className="rounded-full bg-slate-800 px-2 py-1">
              {reason}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default ManagingPanel;
