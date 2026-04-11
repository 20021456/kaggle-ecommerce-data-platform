"use client";

import { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface RefreshButtonProps {
  onRefresh: () => void | Promise<void>;
  autoInterval?: number; // seconds, 0 = off
  className?: string;
}

export function RefreshButton({ onRefresh, autoInterval = 0, className }: RefreshButtonProps) {
  const [spinning, setSpinning] = useState(false);
  const [auto, setAuto] = useState(autoInterval > 0);
  const timer = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const refresh = async () => {
    setSpinning(true);
    try {
      await onRefresh();
    } finally {
      setTimeout(() => setSpinning(false), 600);
    }
  };

  useEffect(() => {
    if (auto && autoInterval > 0) {
      timer.current = setInterval(() => { refresh(); }, autoInterval * 1000);
    }
    return () => clearInterval(timer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto, autoInterval]);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Button variant="outline" size="sm" onClick={refresh} disabled={spinning}>
        <RefreshCw size={14} className={cn("mr-1.5", spinning && "animate-spin")} />
        Refresh
      </Button>
      {autoInterval > 0 && (
        <button
          type="button"
          onClick={() => setAuto((v) => !v)}
          className={cn(
            "text-xs px-2 py-1 rounded-md border",
            auto ? "bg-emerald-50 border-emerald-300 text-emerald-700" : "bg-gray-50 text-gray-500",
          )}
        >
          Auto {auto ? "ON" : "OFF"}
        </button>
      )}
    </div>
  );
}
