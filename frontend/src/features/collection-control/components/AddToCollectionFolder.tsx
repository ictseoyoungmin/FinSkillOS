import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { addFolderSymbol, fetchCollectionControl } from "../api";
import type { CollectionControlData } from "../types";
import { collectionControlFixture } from "@/mocks/fixtures/collectionControl.fixture";

const QUERY_KEY = ["collection-control"];

/**
 * Compact "track this ticker in a collection folder" affordance (idea U1).
 *
 * Reusable across product tabs (currently Market Kernel). Backed by the
 * collection-control API, which subscribes the ticker and links it to the
 * chosen folder in one call — so a symbol on screen becomes worker-tracked in a
 * single click. Writes to the shared ["collection-control"] cache so the Ops
 * Collection Control surface reflects the change immediately.
 */
export function AddToCollectionFolder({ ticker }: { ticker: string }): JSX.Element {
  const queryClient = useQueryClient();
  const normalized = ticker.trim().toUpperCase();
  const [folderId, setFolderId] = useState("");
  const [note, setNote] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  const { data } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: ({ signal }) => fetchCollectionControl(signal),
    placeholderData: collectionControlFixture,
  });
  const folders = (data ?? collectionControlFixture).folders;
  const selected = folderId || folders[0]?.id || "";
  const current = folders.find((folder) => folder.id === selected);
  const alreadyMember = useMemo(
    () => current?.members.some((member) => member.ticker === normalized) ?? false,
    [current, normalized],
  );

  useEffect(() => {
    // A fresh symbol clears any prior confirmation.
    setNote(null);
  }, [normalized]);

  const mutation = useMutation({
    mutationFn: (targetFolderId: string) => addFolderSymbol(targetFolderId, normalized),
    onSuccess: (result: CollectionControlData, targetFolderId) => {
      queryClient.setQueryData(QUERY_KEY, result);
      const folder = result.folders.find((item) => item.id === targetFolderId);
      setNote({ tone: "success", text: `${normalized} tracked in ${folder?.name ?? "folder"}.` });
    },
    onError: () => {
      setNote({ tone: "error", text: "Could not add to folder." });
    },
  });

  const disabled = !selected || !normalized || mutation.isPending || alreadyMember;

  return (
    <div className="fso-add-to-folder" data-testid="add-to-folder">
      <label className="fso-add-to-folder-label" htmlFor="add-to-folder-select">
        Track in
      </label>
      <select
        id="add-to-folder-select"
        className="fso-add-to-folder-select"
        value={selected}
        disabled={mutation.isPending || folders.length === 0}
        data-testid="add-to-folder-select"
        onChange={(event) => {
          setFolderId(event.target.value);
          setNote(null);
        }}
      >
        {folders.length === 0 ? (
          <option value="">No folders</option>
        ) : (
          folders.map((folder) => (
            <option key={folder.id} value={folder.id}>
              {folder.name}
              {folder.isSystem ? " (System)" : ""}
            </option>
          ))
        )}
      </select>
      <button
        type="button"
        className="fso-add-to-folder-btn"
        disabled={disabled}
        data-testid="add-to-folder-button"
        onClick={() => mutation.mutate(selected)}
      >
        {alreadyMember ? "In folder" : "Add"}
      </button>
      {note ? (
        <span
          className="fso-add-to-folder-note"
          data-tone={note.tone}
          data-testid="add-to-folder-note"
          role="status"
        >
          {note.text}
        </span>
      ) : null}
    </div>
  );
}
