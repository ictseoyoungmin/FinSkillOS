import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  applyImportPositions,
  previewImportPositions,
} from "@/features/portfolio/api";
import type {
  MissionControlData,
  PortfolioImportResult,
} from "@/features/portfolio/types";
import { sendAgentChat } from "../api";
import type { ChatMessageVM, ProposedActionVM } from "../types";
import "./agent-chat-widget.css";

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  action?: ProposedActionVM | null;
}

const GREETING: ChatTurn = {
  role: "assistant",
  content:
    "Hi — I record holdings, trades, and watchlists. Paste your holdings and " +
    "I'll prepare an import for you to confirm. I don't give buy/sell advice.",
};

/**
 * Floating agent chat widget (v3 Phase 11 / Slice 192). Talks to
 * /api/agent/chat on the active LLM provider; when the agent proposes a
 * portfolio import, it is previewed (dry-run) and applied only on confirm via
 * the existing audited import. Descriptive bookkeeping only.
 */
export function AgentChatWidget() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([GREETING]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [provider, setProvider] = useState<string>("");
  const [preview, setPreview] = useState<Record<number, PortfolioImportResult>>({});
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [turns, open]);

  const onSend = async () => {
    const text = input.trim();
    if (text === "" || busy) return;
    const userTurn: ChatTurn = { role: "user", content: text };
    const history: ChatMessageVM[] = [...turns, userTurn].map(
      (t): ChatMessageVM => ({ role: t.role, content: t.content }),
    );
    setTurns((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setBusy(true);
    try {
      const result = await sendAgentChat(history);
      setProvider(result.provider);
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: result.reply, action: result.proposedAction },
      ]);
    } catch {
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: "The agent is unreachable right now." },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const onPreview = async (idx: number, action: ProposedActionVM) => {
    setBusy(true);
    try {
      const result = await previewImportPositions(action.normalizedCsv);
      setPreview((p) => ({ ...p, [idx]: result }));
    } finally {
      setBusy(false);
    }
  };

  const onConfirm = async (idx: number, action: ProposedActionVM) => {
    setBusy(true);
    try {
      const result = await applyImportPositions(action.normalizedCsv);
      if (result.snapshot) {
        queryClient.setQueryData<MissionControlData>(
          ["mission-control"],
          result.snapshot,
        );
      }
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Applied — ${result.adds} added, ${result.updates} updated.`,
        },
      ]);
      setPreview((p) => {
        const next = { ...p };
        delete next[idx];
        return next;
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={`fso-chat-widget${open ? " fso-chat-open" : ""}`}>
      <div className="fso-chat-panel" role="dialog" aria-label="Agent chat">
        <div className="fso-chat-header">
          <span className="fso-chat-dot" />
          <span className="fso-chat-title">Agent</span>
          <span className="fso-chat-model">{provider || "llm"}</span>
          <button
            className="fso-chat-min"
            title="New chat"
            onClick={() => {
              setTurns([GREETING]);
              setPreview({});
            }}
          >
            ↺
          </button>
          <button
            className="fso-chat-min"
            title="Minimize"
            onClick={() => setOpen(false)}
          >
            ─
          </button>
        </div>

        <div className="fso-chat-messages" ref={scrollRef}>
          {turns.map((turn, idx) => (
            <div key={idx} className={`fso-chat-msg fso-chat-${turn.role}`}>
              <div className="fso-chat-bubble">{turn.content}</div>
              {turn.action && turn.action.rowCount > 0 ? (
                <div className="fso-chat-action" data-testid="chat-proposed-action">
                  <div className="fso-chat-action-head">
                    {turn.action.summary}
                  </div>
                  {turn.action.warnings.length > 0 ? (
                    <div className="fso-chat-action-warn">
                      {turn.action.warnings.length} warning(s)
                    </div>
                  ) : null}
                  {preview[idx] ? (
                    <button
                      className="fso-chat-confirm"
                      disabled={busy}
                      onClick={() => onConfirm(idx, turn.action!)}
                      data-testid="chat-action-confirm"
                    >
                      Confirm — {preview[idx].adds} add / {preview[idx].updates}{" "}
                      update
                    </button>
                  ) : (
                    <button
                      className="fso-chat-preview"
                      disabled={busy}
                      onClick={() => onPreview(idx, turn.action!)}
                      data-testid="chat-action-preview"
                    >
                      Preview import ({turn.action.rowCount} holdings)
                    </button>
                  )}
                </div>
              ) : null}
            </div>
          ))}
          {busy ? <div className="fso-chat-typing">…</div> : null}
        </div>

        <div className="fso-chat-input-row">
          <textarea
            className="fso-chat-textarea"
            value={input}
            placeholder="Message the agent — or paste holdings…"
            rows={1}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void onSend();
              }
            }}
            data-testid="agent-chat-input"
          />
          <button
            className="fso-chat-send"
            disabled={busy || input.trim() === ""}
            onClick={() => void onSend()}
            data-testid="agent-chat-send"
          >
            ➤
          </button>
        </div>
      </div>

      <button
        className="fso-chat-fab"
        onClick={() => setOpen((o) => !o)}
        title="Agent chat"
        data-testid="agent-chat-fab"
      >
        {open ? "✕" : "💬"}
      </button>
    </div>
  );
}
