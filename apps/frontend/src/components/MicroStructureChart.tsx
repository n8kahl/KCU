import type { Tile } from "../types";

type Props = {
  tile: Tile;
  bars?: number;
  width?: number;
  height?: number;
  highlightEntry?: boolean;
};

export default function MicroStructureChart({ tile, bars = 12, width = 160, height = 64, highlightEntry = true }: Props) {
  const chartBars = tile.bars.slice(-bars);
  const closes = chartBars.map((bar) => bar.c ?? bar.o ?? 0);
  const prices = chartBars.flatMap((bar) => [bar.h ?? bar.c ?? 0, bar.l ?? bar.c ?? 0]);
  const minPrice = Math.min(...prices, ...closes, 0);
  const maxPrice = Math.max(...prices, ...closes, 1);
  const span = maxPrice - minPrice || 1;
  const yFor = (value: number | null | undefined) => {
    const price = value ?? minPrice;
    return height - ((price - minPrice) / span) * height;
  };
  const xFor = (index: number) => (chartBars.length <= 1 ? width : (index / (chartBars.length - 1)) * width);
  const lineFor = (series: (number | null | undefined)[]) => series.map((value, idx) => `${xFor(idx)},${yFor(value)}`).join(" ");
  const ema8 = tile.ema8.slice(-chartBars.length);
  const ema21 = tile.ema21.slice(-chartBars.length);
  const vwap = tile.vwap.slice(-chartBars.length);
  const entryReady = Boolean(tile.delta_to_entry?.at_entry && tile.patience_candle && highlightEntry);
  const latestClose = closes[closes.length - 1] ?? null;

  return (
    <svg width={width} height={height} className="text-slate-500">
      <polyline fill="none" stroke="rgba(148, 163, 184, 0.25)" strokeWidth={6} strokeLinejoin="round" points={lineFor(closes)} />
      <polyline fill="none" stroke="rgba(16, 185, 129, 0.9)" strokeWidth={2} points={lineFor(ema8)} />
      <polyline fill="none" stroke="rgba(59, 130, 246, 0.8)" strokeWidth={1.5} points={lineFor(ema21)} />
      <polyline fill="none" stroke="rgba(250, 204, 21, 0.7)" strokeDasharray="4 3" strokeWidth={1.2} points={lineFor(vwap)} />
      {tile.key_levels.slice(0, 3).map((level) => (
        <line key={level.label} x1={0} x2={width} y1={yFor(level.price)} y2={yFor(level.price)} stroke="rgba(255,255,255,0.15)" strokeDasharray="2 4" />
      ))}
      {entryReady && closes.length > 0 && (
        <circle cx={xFor(closes.length - 1)} cy={yFor(latestClose)} r={5} fill="#22c55e" stroke="#064e3b" strokeWidth={1} />
      )}
    </svg>
  );
}
