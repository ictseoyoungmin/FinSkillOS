import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { OS_NAV_ITEMS } from "./nav-config";
import "./os-command-palette.css";

export interface OsCommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function OsCommandPalette({ open, onClose }: OsCommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input + reset query each time the palette opens.
  useEffect(() => {
    if (open) {
      setQuery("");
      const handle = window.setTimeout(() => inputRef.current?.focus(), 0);
      return () => window.clearTimeout(handle);
    }
    return undefined;
  }, [open]);

  // Close on Esc, navigate on Enter.
  useEffect(() => {
    if (!open) return undefined;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return OS_NAV_ITEMS;
    return OS_NAV_ITEMS.filter(
      (item) =>
        item.label.toLowerCase().includes(needle) ||
        item.description.toLowerCase().includes(needle),
    );
  }, [query]);

  if (!open) return null;

  return (
    <div
      className="fso-command-backdrop"
      data-testid="command-palette"
      role="dialog"
      aria-modal="true"
      aria-label="FinSkillOS command drawer"
      onClick={onClose}
    >
      <div
        className="fso-command-panel"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="fso-command-input-row">
          <span className="fso-command-glyph" aria-hidden>⌘</span>
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Type to filter modules…"
            className="fso-command-input"
            data-testid="command-palette-input"
            onKeyDown={(event) => {
              if (event.key === "Enter" && results[0]) {
                event.preventDefault();
                navigate(results[0].path);
                onClose();
              }
            }}
          />
          <button
            type="button"
            className="fso-command-close"
            onClick={onClose}
            aria-label="Close command drawer"
          >
            <span aria-hidden>×</span>
          </button>
        </div>

        <ul className="fso-command-list" role="listbox">
          {results.length === 0 ? (
            <li className="fso-command-empty">No modules match this filter.</li>
          ) : (
            results.map((item) => (
              <li key={item.key}>
                <button
                  type="button"
                  className="fso-command-item"
                  data-testid={`command-item-${item.key}`}
                  onClick={() => {
                    navigate(item.path);
                    onClose();
                  }}
                >
                  <span className="fso-command-icon" aria-hidden>
                    {item.iconChar}
                  </span>
                  <span className="fso-command-meta">
                    <span className="fso-command-title">Open {item.label}</span>
                    <small className="fso-command-sub">{item.description}</small>
                  </span>
                  <code className="fso-command-go">GO</code>
                </button>
              </li>
            ))
          )}
        </ul>

        <div className="fso-command-footer">
          Navigation only — FinSkillOS does not expose execution controls.
        </div>
      </div>
    </div>
  );
}
