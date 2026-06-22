import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Panel } from "@/shared/ui";
import { deleteSpec, listSavedSpecs, saveSpec } from "../api";

export interface QuantSavedPanelProps {
  /** The currently-shown custom spec (if the tab is on a CUSTOM run), else null. */
  customSpec: Record<string, unknown> | null;
  onLoad: (savedId: string) => void;
}

/**
 * Saved strategies: persist the current agent-authored spec and re-run any saved
 * one later. Loading deep-links the tab to ?saved=<id>. Descriptive — not advice.
 */
export function QuantSavedPanel({ customSpec, onLoad }: QuantSavedPanelProps) {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["quant-saved"],
    queryFn: ({ signal }) => listSavedSpecs(signal),
  });

  const save = useMutation({
    mutationFn: () => saveSpec(customSpec as Record<string, unknown>),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["quant-saved"] }),
  });
  const remove = useMutation({
    mutationFn: (id: string) => deleteSpec(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["quant-saved"] }),
  });

  const specs = data?.specs ?? [];

  return (
    <Panel title="Saved strategies" testId="quant-saved">
      {customSpec ? (
        <button
          className="fso-chat-confirm"
          disabled={save.isPending}
          onClick={() => save.mutate()}
          data-testid="quant-save-current"
        >
          {save.isPending ? "저장 중…" : "현재 전략 저장"}
        </button>
      ) : (
        <p className="fso-quant-note">
          agent가 설계한 전략을 보고 있을 때 여기서 저장할 수 있습니다.
        </p>
      )}
      {specs.length > 0 ? (
        <ul className="fso-quant-saved-list" data-testid="quant-saved-list">
          {specs.map((s) => (
            <li key={s.id}>
              <button
                className="fso-quant-saved-load"
                onClick={() => onLoad(s.id)}
                title="이 전략 불러오기"
              >
                <strong>{s.name}</strong> · {s.ticker}
              </button>
              <button
                className="fso-quant-saved-del"
                disabled={remove.isPending}
                onClick={() => remove.mutate(s.id)}
                aria-label={`${s.name} 삭제`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="fso-quant-empty">저장된 전략이 없습니다.</p>
      )}
    </Panel>
  );
}
