import { useEffect, useMemo, useState } from "react";

const SESSION_GUIDELINES: Record<string, string> = {
  Premarket: "Prep levels, pre-plan risk.",
  "Open I": "Trade playbook setups with full size.",
  Midday: "Fade noise; focus on A+ only.",
  Late: "Protect gains, scale plans deliberately.",
  Afterhours: "Review + log, no new risk.",
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
  if (minutes < 660) return "Open I"; // 9:30-11:00
  if (minutes < 870) return "Midday"; // 11:00-14:30
  if (minutes < 960) return "Late"; // 14:30-16:00
  return "Afterhours";
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
