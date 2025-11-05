import clsx from "clsx";

type Level = { label?: string; price?: number };

type Props = {
  closes: number[];
  levels?: Level[];
  managing?: { targets?: { label?: string; price?: number }[] } | null;
};

const HEIGHT = 50;
const WIDTH = 100;

export default function MiniCandles({ closes, levels = [], managing }: Props) {
  const points = closes.slice(-5);
  if (points.length < 2) {
    return <div className="h-12 w-full rounded border border-slate-800 bg-slate-950/40" />;
  }
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const scaleY = (value: number) => ((max - value) / span) * HEIGHT;
  const candleWidth = WIDTH / points.length;
  const tps = managing?.targets?.slice?.(0, 2) || [];

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-12 w-full">
      {levels
        .filter((lvl) => typeof lvl?.price === "number")
        .slice(0, 3)
        .map((lvl, idx) => {
          const y = scaleY(lvl.price!);
          return (
            <g key={`${lvl.label}-${idx}`}>
              <line x1={0} x2={WIDTH} y1={y} y2={y} stroke="#475569" strokeDasharray="4 3" strokeWidth={0.5} />
              <text x={WIDTH - 2} y={Math.max(8, y - 2)} textAnchor="end" className="fill-slate-500 text-[7px]">
                {lvl.label}
              </text>
            </g>
          );
        })}
      {tps
        .filter((tp) => typeof tp?.price === "number")
        .map((tp, idx) => {
          const y = scaleY(tp.price!);
          return (
            <g key={`tp-${idx}`}>
              <line x1={0} x2={WIDTH} y1={y} y2={y} stroke="#34d399" strokeDasharray="2 2" strokeWidth={0.8} />
              <text x={WIDTH - 2} y={Math.max(10, y - 4)} textAnchor="end" className="fill-emerald-300 text-[7px]">
                {tp.label || `TP${idx + 1}`}
              </text>
            </g>
          );
        })}
      {points.map((close, idx) => {
        const open = idx === 0 ? points[0] : points[idx - 1];
        const x = idx * candleWidth + candleWidth / 2;
        const highY = scaleY(Math.max(open, close));
        const lowY = scaleY(Math.min(open, close));
        const isUp = close >= open;
        const bodyHeight = Math.max(2, Math.abs(highY - lowY));
        return (
          <g key={idx}>
            <line x1={x} x2={x} y1={Math.min(highY, lowY)} y2={Math.max(highY, lowY)} stroke="#cbd5f5" strokeWidth={0.6} />
            <rect
              x={x - candleWidth / 4}
              y={isUp ? lowY : highY}
              width={candleWidth / 2}
              height={bodyHeight}
              className={clsx(isUp ? "fill-emerald-400" : "fill-rose-400")} 
            />
          </g>
        );
      })}
    </svg>
  );
}
