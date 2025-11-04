import clsx from "clsx";

type Props = {
  tickers?: string[];
  selected?: string;
  onSelect: (symbol: string) => void;
};

function TickerCarousel({ tickers = [], selected, onSelect }: Props) {
  if (!tickers.length) return null;
  return (
    <div className="relative">
      <div className="pointer-events-none absolute inset-y-0 left-0 w-8 bg-gradient-to-r from-slate-950 to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-slate-950 to-transparent" />
      <div className="flex snap-x snap-mandatory gap-2 overflow-x-auto pb-2 pl-1 pr-8">
        {tickers.map((symbol) => (
          <button
            key={symbol}
            className={clsx(
              "snap-start rounded-full border px-4 py-2 text-sm font-semibold transition",
              selected === symbol ? "border-emerald-400 bg-emerald-500/10 text-emerald-200" : "border-slate-800 bg-slate-900/60 text-slate-300",
            )}
            onClick={() => onSelect(symbol)}
          >
            {symbol}
          </button>
        ))}
      </div>
    </div>
  );
}

export default TickerCarousel;
