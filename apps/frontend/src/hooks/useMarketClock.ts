import { useEffect, useMemo, useState } from "react";

const SESSION_GUIDELINES: Record<string, string> = {
  Premarket: "Prep only. Mark levels. No early chasing.",
  Open: "Wait for patience candle. Trade only A/A+ with LTP.",
  Midday: "Thin liquidity — be selective. Manage runners only.",
  PowerHour: "Continuation or reversals. Respect VWAP/levels.",
  AfterHours: "No new risk. Journal + review.",
};

type MarketClock = {
  etTime: string;
  session: keyof typeof SESSION_GUIDELINES;
  guidelineText: string;
  warningAfterThree: boolean;
};

function getEtParts(date: Date) {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const parts = formatter.formatToParts(date);
  const hour = Number(parts.find((part) => part.type === "hour")?.value ?? "0");
  const minute = Number(parts.find((part) => part.type === "minute")?.value ?? "0");
  const second = Number(parts.find((part) => part.type === "second")?.value ?? "0");
  const label = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:${String(second).padStart(2, "0")}`;
  return { hour, minute, label };
}

function resolveSession(hour: number, minute: number): MarketClock["session"] {
  const minutes = hour * 60 + minute;
  if (minutes < 570) return "Premarket"; // before 9:30
  if (minutes < 630) return "Open"; // 9:30-10:30
  if (minutes < 870) return "Midday"; // 10:30-14:30
  if (minutes < 960) return "PowerHour"; // 14:30-16:00
  return "AfterHours";
}

export function useMarketClock(): MarketClock {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return useMemo(() => {
    const { hour, minute, label } = getEtParts(now);
    const session = resolveSession(hour, minute);
    const guidelineText = SESSION_GUIDELINES[session];
    const warningAfterThree = hour >= 15;
    return { etTime: label, session, guidelineText, warningAfterThree };
  }, [now]);
}
