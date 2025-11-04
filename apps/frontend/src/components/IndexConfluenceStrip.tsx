import { clsx } from "clsx";

type Props = {
  market?: {
    minuteThrust?: number;
    microChop?: number;
    divergenceZ?: number;
    secVariance?: number;
  } | null;
  orb?: {
    range_pct?: number;
  } | null;
};

const chip = (label: string, value: string, tone: "good" | "warn" | "bad" = "good") => (
  <div
    key={label}
    className={clsx(
      "flex flex-col rounded-lg px-3 py-2 text-xs",
      tone === "good" && "bg-emerald-900/40 text-emerald-200",
      tone === "warn" && "bg-amber-900/50 text-amber-200",
      tone === "bad" && "bg-rose-900/40 text-rose-100",
    )}
  >
    <span className="text-[10px] uppercase tracking-wide text-slate-400">{label}</span>
    <span className="text-sm font-semibold">{value}</span>
  </div>
);

function IndexConfluenceStrip({ market, orb }: Props) {
  if (!market) {
    return (
      <div className="grid grid-cols-2 gap-2 text-xs text-slate-500">
        <span>Index data warming…</span>
      </div>
    );
  }
  const thrust = market.minuteThrust ?? 0;
  const chop = market.microChop ?? 0;
  const div = market.divergenceZ ?? 0;
  const orbPct = orb?.range_pct ?? 0;
  const thrustChip = chip("Thrust", thrust > 0 ? "✓" : "✗", thrust > 0 ? "good" : "warn");
  const chopState = chop < 0.3 ? "Low" : chop < 0.6 ? "Med" : "High";
  const chopChip = chip("Micro-chop", chopState, chop < 0.6 ? "good" : "bad");
  const divChip = chip("ETF vs IDX", `${div.toFixed(2)}σ`, Math.abs(div) <= 0.7 ? "good" : Math.abs(div) <= 1.2 ? "warn" : "bad");
  const pinRisk = orbPct < 0.2 ? "Low" : orbPct < 0.4 ? "Med" : "High";
  const pinChip = chip("Pin risk", pinRisk, pinRisk === "Low" ? "good" : pinRisk === "Med" ? "warn" : "bad");
  const orbChip = chip("ORB % ADR", `${(orbPct * 100).toFixed(0)}%`, orbPct <= 0.35 ? "good" : "warn");

  return <div className="grid grid-cols-2 gap-2 md:grid-cols-5">{[thrustChip, chopChip, divChip, pinChip, orbChip]}</div>;
}

export default IndexConfluenceStrip;
