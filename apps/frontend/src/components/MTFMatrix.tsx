import clsx from "clsx";

type Props = {
  breakdown?: { name: string; score: number }[];
  history?: { score?: number }[];
};

const LANES = [
  { label: "2m", key: "TrendStack" },
  { label: "5m", key: "Levels" },
  { label: "15m", key: "Patience" },
  { label: "60m", key: "ORB" },
  { label: "Daily", key: "Market" },
];

function sparkPoints(values: number[]) {
  if (values.length < 2) return "";
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const span = max - min || 1;
  return values
    .map((val, idx) => {
      const x = (idx / (values.length - 1)) * 100;
      const y = 100 - ((val - min) / span) * 100;
      return `${x},${y}`;
    })
    .join(" ");
}

function MTFMatrix({ breakdown, history }: Props) {
  const map = new Map(breakdown?.map((b) => [b.name, b.score]));
  const trendHistory = history?.slice(-20).map((h) => (h.score ?? 0) / 100) ?? [];
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>MTF alignment</span>
        {trendHistory.length > 1 && (
          <svg className="h-6 w-20" viewBox="0 0 100 100">
            <polyline fill="none" stroke="#34d399" strokeWidth="3" points={sparkPoints(trendHistory) || "0,50 100,50"} />
          </svg>
        )}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs md:grid-cols-5">
        {LANES.map((lane) => {
          const score = map.get(lane.key) ?? 0.5;
          const tone = score > 0.7 ? "good" : score > 0.5 ? "warn" : "bad";
          return (
            <div
              key={lane.label}
              className={clsx(
                "rounded-lg p-2 text-center",
                tone === "good" && "bg-emerald-900/40 text-emerald-100",
                tone === "warn" && "bg-amber-900/40 text-amber-100",
                tone === "bad" && "bg-rose-900/40 text-rose-100",
              )}
            >
              <p className="text-[10px] uppercase tracking-wide text-slate-300">{lane.label}</p>
              <p className="text-base font-semibold">{Math.round(score * 100)}%</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default MTFMatrix;
