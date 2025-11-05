export type AlertAction = "enter" | "take_profit" | "add" | "trim" | "exit";

export type Confluence = {
  name: string;
  score: number;
};

export type LevelDelta = {
  dollars: number | null;
  percent: number | null;
  direction?: "above" | "below" | "at" | null;
  at_entry?: boolean;
};

export type KeyLevel = {
  label: string;
  price: number;
};

export type BarPoint = {
  o: number | null;
  h: number | null;
  l: number | null;
  c: number | null;
  v: number | null;
  t?: string | null;
};

export type Contract = {
  contract: string;
  ticker: string;
  expiry?: string | null;
  strike?: number | null;
  type?: string | null;
  bid?: number | null;
  ask?: number | null;
  mid?: number | null;
  delta?: number | null;
  oi?: number | null;
  spread_quality?: string | null;
};

export type AlertPayload = {
  action: AlertAction;
  symbol: string;
  contract: string;
  price: number;
  grade: string;
  confidence: number;
  level: string;
  stop: number;
  target: number;
  note?: string;
};

export type Tile = {
  symbol: string;
  regime: string;
  grade: string;
  confidence_score: number;
  confidence: Record<string, number>;
  probability_to_action: number;
  band: { label: string; min_score?: number; max_score?: number };
  breakdown: Confluence[];
  options: Record<string, any>;
  options_top3: Contract[];
  rationale: { positives?: string[]; risks?: string[] };
  admin: {
    managing?: Record<string, any>;
    marketMicro?: Record<string, number>;
    lastPrice?: number;
    timing?: { label?: string };
    orb?: Record<string, any>;
    levels?: KeyLevel[];
    atr?: number;
    last_1m_closes?: number[];
  };
  timestamps: { updated: string };
  eta_seconds?: number | null;
  penalties: Record<string, number>;
  bonuses: Record<string, number>;
  history: { ts: string; score: number }[];
  delta_to_entry?: LevelDelta | null;
  key_level_label?: string | null;
  bars: BarPoint[];
  ema8: number[];
  ema21: number[];
  vwap: number[];
  key_levels: KeyLevel[];
  patience_candle: boolean;
};

export type ActiveTradeAlert = {
  id: string;
  action: AlertAction;
  note?: string;
  createdAt: number;
  price?: number;
  grade: string;
  confidence: number;
  level: string;
  stop: number;
  target: number;
};

export type ActiveTrade = {
  contractId: string;
  symbol: string;
  contract: Contract;
  entryPrice?: number;
  latestMid?: number;
  pnlPct?: number;
  timeline: ActiveTradeAlert[];
  lastTemplate?: AlertPayload;
  isClosed: boolean;
  closedAt?: number;
};
