import { useMemo, useRef } from "react";

type SwipeConfig = {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  threshold?: number;
};

function useSwipeNavigation({ onSwipeLeft, onSwipeRight, threshold = 60 }: SwipeConfig) {
  const startX = useRef<number | null>(null);
  const deltaX = useRef(0);

  return useMemo(() => {
    return {
      onTouchStart: (event: React.TouchEvent) => {
        startX.current = event.touches[0].clientX;
        deltaX.current = 0;
      },
      onTouchMove: (event: React.TouchEvent) => {
        if (startX.current === null) return;
        deltaX.current = event.touches[0].clientX - startX.current;
      },
      onTouchEnd: () => {
        if (Math.abs(deltaX.current) < threshold) {
          startX.current = null;
          deltaX.current = 0;
          return;
        }
        if (deltaX.current < 0) {
          onSwipeLeft?.();
        } else {
          onSwipeRight?.();
        }
        startX.current = null;
        deltaX.current = 0;
      },
    } as React.HTMLAttributes<HTMLElement>;
  }, [onSwipeLeft, onSwipeRight, threshold]);
}

export default useSwipeNavigation;
