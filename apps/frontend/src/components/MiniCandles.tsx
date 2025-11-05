type Level = { label?: string; price?: number };

type FibRange = { low: number; high: number };

type ManagingLite = {
  entry?: number;
  targets?: { label?: string; price?: number }[];
  runner?: { trail?: number };
};

type Props = {
  closes: number[];
  levels?: Level[];
  managing?: ManagingLite | null;
  ema?: { e8?: number[]; e21?: number[] } | null;
  sma200?: number[] | null;
  fib?: FibRange | null;
  aPlusEntry?: boolean;
};

const HEIGHT = 50;
const WIDTH = 100;

function average(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((acc, value) => acc + value, 0) / values.length;
}

function sma(series: number[], window: number): number[] {
  return series.map((_, idx) => {
    const start = Math.max(0, idx - window + 1);
    const slice = series.slice(start, idx + 1);
    return average(slice);
  });
}

function ema(series: number[], window: number): number[] {
  if (!series.length) return [];
  const k = 2 / (window + 1);
  return series.reduce<number[]>((acc, value, idx) => {
    if (idx === 0) {
      acc.push(value);
    } else {
      acc.push(value * k + acc[idx - 1] * (1 - k));
    }
    return acc;
  }, []);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export default function MiniCandles({
  closes,
  levels = [],
  managing,
  ema: precomputedEma,
  sma200: precomputedSma200,
  fib,
  aPlusEntry = false,
}: Props) {
  const numericCloses = closes.filter(isFiniteNumber);
  const viewport = numericCloses.slice(-50);
  const visible = viewport.slice(-5);

  if (visible.length < 2) {
    return <div className="h-12 w-full rounded border border-slate-800 bg-slate-950/40" />;
  }

  const targetLines = (managing?.targets ?? []).filter((tp) => isFiniteNumber(tp?.price)).slice(0, 2);
  const keyLevelPrices = levels.filter((lvl) => isFiniteNumber(lvl?.price)).slice(0, 3);

  let fibRange = fib;
  if (!fibRange && viewport.length) {
    const window = viewport.slice(-20);
    if (window.length) {
      const low = Math.min(...window);
      const high = Math.max(...window);
      if (high !== low) {
        fibRange = { low, high };
      }
    }
  }

  const fibs =
    fibRange && fibRange.high !== fibRange.low
      ? [0.236, 0.382, 0.5, 0.618].map((ratio) => fibRange!.high - (fibRange!.high - fibRange!.low) * ratio)
      : [];

  const e8 = (precomputedEma?.e8 ?? ema(viewport, 8)).slice(-5);
  const e21 = (precomputedEma?.e21 ?? ema(viewport, 21)).slice(-5);
  const s200 = (precomputedSma200 ?? sma(numericCloses, 200)).slice(-5);

  const scalingValues: number[] = [...visible];
  const pushValue = (value?: number | null) => {
    if (isFiniteNumber(value)) scalingValues.push(value);
  };
  keyLevelPrices.forEach((lvl) => pushValue(lvl.price));
  targetLines.forEach((tp) => pushValue(tp.price));
  pushValue(managing?.entry);
  pushValue(managing?.runner?.trail);
  fibs.forEach((value) => pushValue(value));
  e8.forEach(pushValue);
  e21.forEach(pushValue);
  s200.forEach(pushValue);

  const min = Math.min(...scalingValues);
  const max = Math.max(...scalingValues);
  const span = max - min || 1;
  const scaleY = (value: number) => ((max - value) / span) * HEIGHT;
  const candleWidth = WIDTH / visible.length;

  const lineSeries = [
    { data: e8, stroke: "#10b981", width: 0.8 },
    { data: e21, stroke: "#0ea5e9", width: 0.8 },
    { data: s200, stroke: "#e5e7eb", width: 0.6 },
  ];

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-12 w-full">
      {keyLevelPrices.map((lvl, idx) => {
        const y = scaleY(lvl.price!);
        return (
          <g key={`lvl-${idx}`}>
            <line x1={0} x2={WIDTH} y1={y} y2={y} stroke="#475569" strokeDasharray="4 3" strokeWidth={0.5} />
            <text x={WIDTH - 2} y={Math.max(8, y - 2)} textAnchor="end" className="fill-slate-500 text-[7px]">
              {lvl.label}
            </text>
          </g>
        );
      })}

      {targetLines.map((tp, idx) => {
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

      {isFiniteNumber(managing?.entry) && (
        <line x1={0} x2={WIDTH} y1={scaleY(managing.entry!)} y2={scaleY(managing.entry!)} stroke="#22d3ee" strokeWidth={0.8} />
      )}
      {isFiniteNumber(managing?.runner?.trail) && (
        <line
          x1={0}
          x2={WIDTH}
          y1={scaleY(managing.runner!.trail!)}
          y2={scaleY(managing.runner!.trail!)}
          stroke="#f97316"
          strokeDasharray="3 2"
          strokeWidth={0.8}
        />
      )}

      {fibs.map((value, idx) => (
        <line key={`fib-${idx}`} x1={0} x2={WIDTH} y1={scaleY(value)} y2={scaleY(value)} stroke="#64748b" strokeDasharray="1 2" strokeWidth={0.5} />
      ))}

      {lineSeries.map(({ data, stroke, width }, idx) => {
        if (data.length < 2) return null;
        const d = data
          .map((value, pointIdx) => {
            const x = (pointIdx / (data.length - 1 || 1)) * WIDTH;
            return `${x},${scaleY(value)}`;
          })
          .join(" ");
        return <polyline key={`series-${idx}`} fill="none" stroke={stroke} strokeWidth={width} points={d} />;
      })}

      {visible.map((close, idx) => {
        const open = idx === 0 ? visible[0] : visible[idx - 1];
        const x = idx * candleWidth + candleWidth / 2;
        const highY = scaleY(Math.max(open, close));
        const lowY = scaleY(Math.min(open, close));
        const isUp = close >= open;
        const bodyHeight = Math.max(2, Math.abs(highY - lowY));
        const isLast = idx === visible.length - 1;
        const fill = isLast && aPlusEntry ? "#22c55e" : isUp ? "#34d399" : "#fb7185";
        return (
          <g key={`candle-${idx}`}>
            <line x1={x} x2={x} y1={Math.min(highY, lowY)} y2={Math.max(highY, lowY)} stroke="#cbd5f5" strokeWidth={0.6} />
            <rect x={x - candleWidth / 4} y={isUp ? lowY : highY} width={candleWidth / 2} height={bodyHeight} fill={fill} />
          </g>
        );
      })}
    </svg>
  );
}
