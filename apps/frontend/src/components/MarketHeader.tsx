import type { ReactNode } from "react";
import type { WsStatus } from "../api/client";
import { useMarketClock } from "../hooks/useMarketClock";

type Props = {
  status: WsStatus;
  lastHeartbeatAgo: number;
  children?: ReactNode;
};

const STATUS_LABEL: Record<WsStatus, string> = {
  online: "Live",
  connecting: "Connecting…",
  offline: "Offline",
};

const STATUS_TONE: Record<WsStatus, string> = {
  online: "bg-emerald-500/20 text-emerald-200 border-emerald-400/40",
  connecting: "bg-amber-500/10 text-amber-200 border-amber-400/30",
  offline: "bg-rose-500/10 text-rose-200 border-rose-400/30",
};

export default function MarketHeader({ status, lastHeartbeatAgo, children }: Props) {
  const { etTime, session, guidelineText, warningAfterThree } = useMarketClock();

  return (
    <header className="sticky top-0 z-10 border-b border-slate-900/80 bg-slate-950/70 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">KCU LTP</p>
            <h1 className="text-2xl font-semibold text-white">Admin Copilot</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${STATUS_TONE[status]}`}>
              <span className="h-2 w-2 rounded-full bg-current" />
              {STATUS_LABEL[status]} · {lastHeartbeatAgo}s
            </span>
            <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-200">
              {etTime} ET · {session}
            </span>
            {warningAfterThree && <span className="rounded-full bg-amber-500/20 px-3 py-1 text-[11px] text-amber-200">After 15:00 – caution</span>}
          </div>
          <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 px-4 py-2">
            <p className="text-[11px] uppercase tracking-wide text-slate-500">KCU Trading Guidelines</p>
            <p className="text-sm text-slate-200">{guidelineText}</p>
          </div>
        </div>
        {children ? <div className="w-full sm:w-auto">{children}</div> : null}
      </div>
    </header>
  );
}
