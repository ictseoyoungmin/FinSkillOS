import { useCallback, useEffect, useRef, useState } from "react";
import { Panel } from "@/shared/ui";
import type { QuantEquityPoint, QuantMarker } from "../types";
import { QuantPriceReplayChart } from "./QuantPriceReplayChart";

export interface QuantReplayPanelProps {
  curve: QuantEquityPoint[];
  markers: QuantMarker[];
  ticker: string;
  /** Auto-play once when the data first arrives (the agent-design deep-link). */
  autoPlay?: boolean;
}

const TICK_MS = 45;

/**
 * Streams the simulation through time: the price line draws left→right and the
 * 노출 시작/해제 markers appear as they occur. Play / pause / restart; descriptive
 * only (exposure ON/OFF, never buy/sell).
 */
export function QuantReplayPanel({
  curve,
  markers,
  ticker,
  autoPlay = false,
}: QuantReplayPanelProps) {
  const n = curve.length;
  const [frame, setFrame] = useState(n);
  const [playing, setPlaying] = useState(false);
  const timer = useRef<number | null>(null);

  const stepBy = Math.max(1, Math.round(n / 60));

  const clearTimer = useCallback(() => {
    if (timer.current !== null) {
      window.clearInterval(timer.current);
      timer.current = null;
    }
  }, []);

  const play = useCallback(() => {
    if (n === 0) return;
    setFrame((f) => (f >= n ? 0 : f));
    setPlaying(true);
  }, [n]);

  // Reset to a full (static) view whenever the dataset changes, then optionally
  // auto-play the new run once.
  useEffect(() => {
    clearTimer();
    setFrame(n);
    setPlaying(false);
    if (autoPlay && n > 1) {
      setFrame(0);
      setPlaying(true);
    }
  }, [curve, n, autoPlay, clearTimer]);

  useEffect(() => {
    if (!playing) {
      clearTimer();
      return;
    }
    timer.current = window.setInterval(() => {
      setFrame((f) => {
        const next = f + stepBy;
        if (next >= n) {
          setPlaying(false);
          return n;
        }
        return next;
      });
    }, TICK_MS);
    return clearTimer;
  }, [playing, n, stepBy, clearTimer]);

  const atEnd = frame >= n;
  const pct = n > 0 ? Math.round((Math.min(frame, n) / n) * 100) : 0;

  return (
    <Panel title="Time-series replay" testId="quant-replay">
      <p className="fso-quant-note">
        {ticker} 가격을 시간순으로 재생 · ▲ 노출 시작 / ▼ 노출 해제 마커 · 음영 = 노출 ON 구간
        (시뮬레이션, 매매 권유 아님)
      </p>
      <QuantPriceReplayChart
        curve={curve}
        markers={markers}
        visibleCount={frame}
        ticker={ticker}
      />
      <div className="fso-quant-replay-controls">
        {playing ? (
          <button
            className="fso-chat-confirm"
            onClick={() => setPlaying(false)}
            data-testid="quant-replay-pause"
          >
            ⏸ 일시정지
          </button>
        ) : (
          <button
            className="fso-chat-confirm"
            onClick={play}
            data-testid="quant-replay-play"
          >
            {atEnd ? "↻ 다시 재생" : "▶ 재생"}
          </button>
        )}
        <button
          className="fso-chat-preview"
          onClick={() => {
            setPlaying(false);
            setFrame(n);
          }}
          data-testid="quant-replay-full"
        >
          전체 보기
        </button>
        <span className="fso-quant-replay-progress" aria-hidden>
          <span style={{ width: `${pct}%` }} />
        </span>
        <span className="fso-quant-replay-frame">
          {Math.min(frame, n)} / {n} bar
        </span>
      </div>
    </Panel>
  );
}
