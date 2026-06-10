import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  applyImportPositions,
  previewImportPositions,
  updateSnapshotBaseline,
} from "@/features/portfolio/api";
import type { MissionControlData } from "@/features/portfolio/types";
import {
  applyTradeImport,
  previewTradeImport,
} from "@/features/trades/api";
import {
  addFolderSymbol,
  createFolder,
  fetchCollectionControl,
  removeFolderSymbol,
} from "@/features/collection-control/api";
import { runSystemOpsProtocol } from "@/features/system-ops/api";
import type { ProtocolKey } from "@/features/system-ops/types";

// Protocols → the React-Query keys to refresh after a successful run.
const PROTOCOL_REFRESH: Record<string, string[]> = {
  recompute_regime: ["control-room", "market-kernel", "mission-control"],
  run_risk_guards: ["risk-firewall", "control-room"],
  refresh_news: ["news-intelligence", "control-room"],
  refresh_events: ["event-radar", "control-room"],
  refresh_market_data: ["market-kernel", "control-room"],
  calculate_indicators: ["market-kernel", "symbol-lab"],
};
import {
  fetchAgentProviders,
  sendAgentChat,
  switchAgentProvider,
} from "../api";
import type {
  AgentProvidersResponse,
  LLMProviderKind,
  ProposedActionVM,
} from "../types";
import "./agent-chat-widget.css";

interface Attachment {
  id: string;
  dataUrl: string;
  name: string;
}

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  time: string;
  images?: string[];
  actions?: ProposedActionVM[];
}

const GREETING: ChatTurn = {
  role: "assistant",
  content:
    "Hi — I record holdings, trades, and watchlists. Paste or attach a " +
    "screenshot of your holdings and I'll prepare an import for you to confirm. " +
    "I don't give buy/sell advice.",
  time: now(),
};

function now(): string {
  return new Date().toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function loadStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? { ...fallback, ...JSON.parse(raw) } : fallback;
  } catch {
    return fallback;
  }
}

/** Render **bold** / `code` inline, safely (no raw HTML). */
function renderInline(text: string, keyBase: string) {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((seg, j) => {
    if (seg.startsWith("**") && seg.endsWith("**")) {
      return <strong key={`${keyBase}-${j}`}>{seg.slice(2, -2)}</strong>;
    }
    if (seg.startsWith("`") && seg.endsWith("`")) {
      return <code key={`${keyBase}-${j}`}>{seg.slice(1, -1)}</code>;
    }
    return <span key={`${keyBase}-${j}`}>{seg}</span>;
  });
}

/** Minimal, safe markdown: headings, *, -, and 1. lists, **bold**, `code`. */
function renderRich(text: string) {
  return text.split("\n").map((line, i) => {
    const trimmed = line.trimStart();
    const heading = /^#{1,6}\s+/.test(trimmed);
    const bullet = /^[*-]\s+/.test(trimmed);
    const numbered = /^(\d+)\.\s+/.exec(trimmed);
    if (heading) {
      return (
        <div key={i} className="fso-chat-h">
          {renderInline(trimmed.replace(/^#{1,6}\s+/, ""), `${i}`)}
        </div>
      );
    }
    const body = bullet
      ? trimmed.replace(/^[*-]\s+/, "")
      : numbered
        ? trimmed.replace(/^\d+\.\s+/, "")
        : line;
    const segs = renderInline(body, `${i}`);
    return bullet || numbered ? (
      <div key={i} className="fso-chat-li">
        {bullet ? "• " : `${numbered![1]}. `}
        {segs}
      </div>
    ) : (
      <div key={i}>{segs.length ? segs : <br />}</div>
    );
  });
}

/**
 * Floating agent chat widget (v3 Phase 11 / Slice 192-193). Mockup-parity:
 * drag-to-move, in-widget provider picker, screenshot attach (drag-drop +
 * preview), auto-grow input, typing indicator, timestamps. Talks to
 * /api/agent/chat on the active provider; a proposed import is previewed
 * (dry-run) and applied only on confirm. Descriptive bookkeeping only.
 */
export function AgentChatWidget() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([GREETING]);
  const [input, setInput] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [busy, setBusy] = useState(false);
  const [dragHover, setDragHover] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [preview, setPreview] = useState<Record<string, string>>({});
  // Actions that have already been applied/run — prevents double-apply.
  const [applied, setApplied] = useState<Set<string>>(new Set());
  const [pos, setPos] = useState(() => loadStored("fso-chat-pos", { right: 24, bottom: 24 }));
  const [size, setSize] = useState(() => loadStored("fso-chat-size", { w: 520, h: 600 }));

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const dragState = useRef<{ x: number; y: number; r: number; b: number } | null>(
    null,
  );
  const resizeState = useRef<{ x: number; y: number; w: number; h: number } | null>(
    null,
  );

  useEffect(() => {
    try {
      localStorage.setItem("fso-chat-pos", JSON.stringify(pos));
    } catch {
      /* ignore */
    }
  }, [pos]);
  useEffect(() => {
    try {
      localStorage.setItem("fso-chat-size", JSON.stringify(size));
    } catch {
      /* ignore */
    }
  }, [size]);

  const providersQuery = useQuery({
    queryKey: ["agent-providers"],
    queryFn: ({ signal }) => fetchAgentProviders(signal),
  });
  const providers = providersQuery.data;

  const switchMutation = useMutation({
    mutationFn: (kind: LLMProviderKind) => switchAgentProvider(kind),
    onSuccess: (next: AgentProvidersResponse) => {
      queryClient.setQueryData(["agent-providers"], next);
      setPickerOpen(false);
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [turns, open]);

  // Close the provider picker on outside click / Escape.
  useEffect(() => {
    if (!pickerOpen) return;
    const onDown = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest(".fso-chat-picker") && !target.closest(".fso-chat-model")) {
        setPickerOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPickerOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [pickerOpen]);

  // Drag-to-move (header) + drag-to-resize (top-left handle).
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (dragState.current) {
        const d = dragState.current;
        setPos({
          right: Math.max(8, d.r - (e.clientX - d.x)),
          bottom: Math.max(8, d.b - (e.clientY - d.y)),
        });
      } else if (resizeState.current) {
        const r = resizeState.current;
        // Top-left handle on a bottom-right-anchored panel: left/up grows it.
        setSize({
          w: Math.max(340, Math.min(window.innerWidth * 0.92, r.w + (r.x - e.clientX))),
          h: Math.max(360, Math.min(window.innerHeight * 0.85, r.h + (r.y - e.clientY))),
        });
      }
    };
    const onUp = () => {
      dragState.current = null;
      resizeState.current = null;
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  const startDrag = (e: React.MouseEvent) => {
    dragState.current = { x: e.clientX, y: e.clientY, r: pos.right, b: pos.bottom };
    document.body.style.userSelect = "none";
  };

  const startResize = (e: React.MouseEvent) => {
    e.stopPropagation();
    resizeState.current = { x: e.clientX, y: e.clientY, w: size.w, h: size.h };
    document.body.style.userSelect = "none";
  };

  const addFiles = (files: FileList | File[]) => {
    Array.from(files)
      .filter((f) => f.type.startsWith("image/"))
      .forEach((file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const dataUrl = String(e.target?.result ?? "");
          setAttachments((prev) => [
            ...prev,
            { id: `${Date.now()}-${Math.random()}`, dataUrl, name: file.name },
          ]);
        };
        reader.readAsDataURL(file);
      });
  };

  const autoGrow = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  };

  const submit = async (text: string, images: string[]) => {
    if ((text === "" && images.length === 0) || busy) return;
    const userTurn: ChatTurn = { role: "user", content: text, time: now(), images };
    const history = [...turns, userTurn]
      .filter((t) => t.role === "user" || t.role === "assistant")
      .map((t) => ({ role: t.role, content: t.content, images: t.images ?? [] }));
    setTurns((prev) => [...prev, userTurn]);
    setBusy(true);
    try {
      const result = await sendAgentChat(history);
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.reply,
          time: now(),
          actions: result.proposedActions,
        },
      ]);
    } catch {
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: "The agent is unreachable right now.", time: now() },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const onSend = async () => {
    const text = input.trim();
    const images = attachments.map((a) => a.dataUrl);
    if ((text === "" && images.length === 0) || busy) return;
    setInput("");
    setAttachments([]);
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    await submit(text, images);
  };

  // Capture the current cockpit screen (true pixels via the Screen Capture API)
  // and ask the agent to describe it. Needs a vision-capable provider.
  const captureScreen = async () => {
    if (busy) return;
    const md = navigator.mediaDevices;
    if (!md?.getDisplayMedia) {
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Screen capture isn't supported here — drag-drop or attach a " +
            "screenshot with ＋ instead.",
          time: now(),
        },
      ]);
      return;
    }
    try {
      const stream = await md.getDisplayMedia({ video: true, audio: false });
      const video = document.createElement("video");
      video.srcObject = stream;
      await video.play();
      await new Promise((r) => setTimeout(r, 250));
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 1280;
      canvas.height = video.videoHeight || 720;
      canvas.getContext("2d")?.drawImage(video, 0, 0, canvas.width, canvas.height);
      stream.getTracks().forEach((t) => t.stop());
      const dataUrl = canvas.toDataURL("image/jpeg", 0.8);
      await submit("Describe what's on this screen.", [dataUrl]);
    } catch {
      /* user cancelled the share dialog */
    }
  };

  const onPreview = async (pkey: string, action: ProposedActionVM) => {
    setBusy(true);
    try {
      let label: string;
      if (action.kind === "trades_import") {
        const r = await previewTradeImport(action.normalizedCsv);
        label = `${r.valid} valid / ${r.invalid} invalid`;
      } else {
        const r = await previewImportPositions(action.normalizedCsv);
        label = `${r.adds} add / ${r.updates} update`;
      }
      setPreview((p) => ({ ...p, [pkey]: label }));
    } finally {
      setBusy(false);
    }
  };

  const onApplyWatchlist = async (pkey: string, action: ProposedActionVM) => {
    const op = action.watchlist;
    if (!op) return;
    setBusy(true);
    try {
      let data = await fetchCollectionControl();
      let folder = data.folders.find(
        (f) => f.name.toLowerCase() === op.folder.toLowerCase(),
      );
      if (!folder) {
        data = await createFolder(op.folder);
        folder = data.folders.find(
          (f) => f.name.toLowerCase() === op.folder.toLowerCase(),
        );
      }
      if (folder) {
        for (const ticker of op.add) await addFolderSymbol(folder.id, ticker);
        for (const ticker of op.remove) await removeFolderSymbol(folder.id, ticker);
      }
      void queryClient.invalidateQueries({ queryKey: ["collection-control"] });
      const parts: string[] = [];
      if (op.add.length) parts.push(`added ${op.add.join(", ")}`);
      if (op.remove.length) parts.push(`removed ${op.remove.join(", ")}`);
      setApplied((s) => new Set(s).add(pkey));
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Watch folder "${op.folder}" — ${parts.join(", ")}.`,
          time: now(),
        },
      ]);
      setPreview((p) => {
        const next = { ...p };
        delete next[pkey];
        return next;
      });
    } catch {
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: "Couldn't update the watchlist.", time: now() },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const onRunProtocol = async (pkey: string, action: ProposedActionVM) => {
    if (!action.protocol) return;
    setBusy(true);
    try {
      const result = await runSystemOpsProtocol(action.protocol as ProtocolKey);
      (PROTOCOL_REFRESH[action.protocol] ?? []).forEach((key) =>
        queryClient.invalidateQueries({ queryKey: [key] }),
      );
      setApplied((s) => new Set(s).add(pkey));
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `${result.status} — ${result.message}`,
          time: now(),
        },
      ]);
      setPreview((p) => {
        const next = { ...p };
        delete next[pkey];
        return next;
      });
    } catch {
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: "Couldn't run that operation.", time: now() },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const onConfirm = async (pkey: string, action: ProposedActionVM) => {
    setBusy(true);
    try {
      let applied: string;
      if (action.kind === "trades_import") {
        const r = await applyTradeImport(action.normalizedCsv);
        applied = `Recorded ${r.valid} trade entr${r.valid === 1 ? "y" : "ies"}.`;
        void queryClient.invalidateQueries({ queryKey: ["trade-memory"] });
      } else {
        const r = await applyImportPositions(action.normalizedCsv);
        applied = `Applied — ${r.adds} added, ${r.updates} updated.`;
        let snapshot = r.snapshot ?? null;
        // Auto-reconcile the snapshot baseline so the total matches the new
        // positions + cash (avoids the "off by N%" reconciliation error).
        const recon = snapshot?.reconciliation;
        if (recon && recon.status !== "OK") {
          try {
            snapshot = await updateSnapshotBaseline({
              totalValue: recon.reconciledTotal,
              cashValue: recon.cashValue,
            });
            applied += " Baseline reconciled.";
          } catch {
            /* leave the baseline as-is on failure */
          }
        }
        if (snapshot) {
          queryClient.setQueryData<MissionControlData>(
            ["mission-control"],
            snapshot,
          );
        }
      }
      setApplied((s) => new Set(s).add(pkey));
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: applied, time: now() },
      ]);
      setPreview((p) => {
        const next = { ...p };
        delete next[pkey];
        return next;
      });
    } finally {
      setBusy(false);
    }
  };

  const activeProvider = providers?.providers.find(
    (p) => p.kind === providers.active,
  );

  return (
    <div
      className={`fso-chat-widget${open ? " fso-chat-open" : ""}`}
      style={{ right: pos.right, bottom: pos.bottom }}
    >
      <div
        className={`fso-chat-panel${dragHover ? " fso-chat-drag" : ""}`}
        role="dialog"
        aria-label="Agent chat"
        style={{ width: size.w, height: size.h }}
        onDragEnter={(e) => {
          e.preventDefault();
          setDragHover(true);
        }}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node))
            setDragHover(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragHover(false);
          addFiles(e.dataTransfer.files);
        }}
      >
        {dragHover ? (
          <div className="fso-chat-drop-overlay">Drop screenshot here</div>
        ) : null}

        <div
          className="fso-chat-resize"
          onMouseDown={startResize}
          title="Drag to resize"
        />

        <div className="fso-chat-header" onMouseDown={startDrag}>
          <span className="fso-chat-dot" />
          <span className="fso-chat-title">Agent</span>
          <button
            className="fso-chat-model"
            onClick={(e) => {
              e.stopPropagation();
              setPickerOpen((o) => !o);
            }}
            title="Switch model"
          >
            {activeProvider?.label ?? providers?.active ?? "llm"}
            {activeProvider?.vision ? " · 👁" : ""}
          </button>
          <button
            className="fso-chat-min"
            title="New chat"
            onClick={() => {
              setTurns([{ ...GREETING, time: now() }]);
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

        {pickerOpen && providers ? (
          <div className="fso-chat-picker" data-testid="chat-provider-picker">
            {providers.providers.map((p) => (
              <button
                key={p.kind}
                className={`fso-chat-picker-row${
                  p.kind === providers.active ? " fso-chat-picker-active" : ""
                }`}
                disabled={switchMutation.isPending}
                onClick={() => switchMutation.mutate(p.kind)}
              >
                <span className="fso-chat-picker-dot" data-ready={p.ready} />
                <span className="fso-chat-picker-name">
                  {p.label}
                  {p.vision ? " · vision" : ""}
                </span>
                <span className="fso-chat-picker-state">
                  {p.ready ? "ready" : "not ready"}
                </span>
              </button>
            ))}
          </div>
        ) : null}

        <div className="fso-chat-messages" ref={scrollRef}>
          {turns.map((turn, idx) => (
            <div key={idx} className={`fso-chat-msg fso-chat-${turn.role}`}>
              <div className="fso-chat-avatar">
                {turn.role === "assistant" ? "A" : "U"}
              </div>
              <div className="fso-chat-body">
                {turn.content ? (
                  <div className="fso-chat-bubble">
                    {turn.role === "assistant"
                      ? renderRich(turn.content)
                      : turn.content}
                  </div>
                ) : null}
                {turn.images && turn.images.length > 0 ? (
                  <div className="fso-chat-imgs">
                    {turn.images.map((src, i) => (
                      <img key={i} src={src} alt="attachment" />
                    ))}
                  </div>
                ) : null}
                {(turn.actions ?? [])
                  .filter((a) => a.rowCount > 0)
                  .map((action, ai) => {
                    const pkey = `${idx}:${ai}`;
                    return (
                      <div
                        key={ai}
                        className="fso-chat-action"
                        data-testid="chat-proposed-action"
                      >
                        <div className="fso-chat-action-head">{action.summary}</div>
                        {action.warnings.length > 0 ? (
                          <div className="fso-chat-action-warn">
                            {action.warnings.length} warning(s)
                          </div>
                        ) : null}
                        {applied.has(pkey) ? (
                          <span className="fso-chat-done" data-testid="chat-action-done">
                            ✓ Done
                          </span>
                        ) : action.kind === "watch_update" ? (
                          <button
                            className="fso-chat-confirm"
                            disabled={busy}
                            onClick={() => onApplyWatchlist(pkey, action)}
                            data-testid="chat-action-watchlist"
                          >
                            Apply to watchlist
                          </button>
                        ) : action.kind === "run_protocol" ? (
                          <button
                            className="fso-chat-confirm"
                            disabled={busy}
                            onClick={() => onRunProtocol(pkey, action)}
                            data-testid="chat-action-protocol"
                          >
                            Run
                          </button>
                        ) : preview[pkey] ? (
                          <button
                            className="fso-chat-confirm"
                            disabled={busy}
                            onClick={() => onConfirm(pkey, action)}
                            data-testid="chat-action-confirm"
                          >
                            Confirm — {preview[pkey]}
                          </button>
                        ) : (
                          <button
                            className="fso-chat-preview"
                            disabled={busy}
                            onClick={() => onPreview(pkey, action)}
                            data-testid="chat-action-preview"
                          >
                            Preview{" "}
                            {action.kind === "trades_import" ? "trades" : "import"} (
                            {action.rowCount}{" "}
                            {action.kind === "trades_import" ? "trades" : "holdings"})
                          </button>
                        )}
                      </div>
                    );
                  })}
                <span className="fso-chat-time">{turn.time}</span>
              </div>
            </div>
          ))}
          {busy ? (
            <div className="fso-chat-typing">
              <span />
              <span />
              <span />
            </div>
          ) : null}
        </div>

        {attachments.length > 0 ? (
          <div className="fso-chat-strip">
            {attachments.map((a) => (
              <div className="fso-chat-thumb" key={a.id}>
                <img src={a.dataUrl} alt={a.name} />
                <button
                  onClick={() =>
                    setAttachments((prev) => prev.filter((x) => x.id !== a.id))
                  }
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        ) : null}

        <div className="fso-chat-input-row">
          <button
            className="fso-chat-attach"
            title="Attach screenshot"
            onClick={() => fileRef.current?.click()}
          >
            ＋
          </button>
          <button
            className="fso-chat-attach"
            title="Explain the current screen"
            disabled={busy}
            onClick={() => void captureScreen()}
            data-testid="agent-chat-capture"
          >
            🖥
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            multiple
            hidden
            onChange={(e) => {
              if (e.target.files) addFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <textarea
            ref={textareaRef}
            className="fso-chat-textarea"
            value={input}
            placeholder="Message — or paste / attach holdings…"
            rows={1}
            onChange={(e) => {
              setInput(e.target.value);
              autoGrow();
            }}
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
            disabled={busy || (input.trim() === "" && attachments.length === 0)}
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
