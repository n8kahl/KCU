function Sparkline({ data }: { data?: number[] }) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const span = max - min || 1;
  const points = data
    .map((value, idx) => {
      const x = (idx / (data.length - 1)) * 100;
      const y = 100 - ((value - min) / span) * 100;
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg className="h-10 w-full" viewBox="0 0 100 100">
      <polyline fill="none" stroke="#10b981" strokeWidth="3" points={points} />
    </svg>
  );
}

export default Sparkline;
