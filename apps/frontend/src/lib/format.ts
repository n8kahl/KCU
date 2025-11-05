export function formatContractId(contract: string | undefined | null): string {
  if (!contract) return "--";
  const match = contract.match(/^O:(\w+)(\d{2})(\d{2})(\d{2})([CP])0*(\d+)$/);
  if (!match) return contract;
  const [, root, yy, mm, dd, callPut, strikeRaw] = match;
  const year = `20${yy}`;
  const strikeNumber = Number(strikeRaw) / 100;
  const strikeFormatted = Number.isFinite(strikeNumber) ? strikeNumber.toFixed(2).replace(/\.00$/, "") : strikeRaw;
  return `${root} ${year}-${mm}-${dd} ${strikeFormatted}${callPut}`;
}
