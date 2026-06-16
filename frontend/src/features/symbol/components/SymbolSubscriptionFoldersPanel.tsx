import { useMemo, useState } from "react";
import { Panel } from "@/shared/ui";
import type {
  SymbolSubscriptionFolderList,
  SymbolSubscriptionState,
} from "../types";
import "./symbol-subscription-folders-panel.css";

export interface SymbolSubscriptionFoldersPanelProps {
  currentTicker: string;
  folders: SymbolSubscriptionFolderList;
  subscription: SymbolSubscriptionState;
  busy?: boolean;
  onAddToFolder: (folderId: string) => void;
  onCreateFolder: (name: string) => void;
  onRemoveFromFolder: (folderId: string) => void;
}

export function SymbolSubscriptionFoldersPanel({
  currentTicker,
  folders,
  subscription,
  busy = false,
  onAddToFolder,
  onCreateFolder,
  onRemoveFromFolder,
}: SymbolSubscriptionFoldersPanelProps) {
  const [folderName, setFolderName] = useState("");
  const normalizedTicker = currentTicker.toUpperCase();
  const sortedFolders = folders.folders;
  const containingFolderIds = useMemo(
    () =>
      new Set(
        sortedFolders
          .filter((folder) =>
            folder.members.some((member) => member.ticker === normalizedTicker),
          )
          .map((folder) => folder.id),
      ),
    [normalizedTicker, sortedFolders],
  );

  const canCreate = folderName.trim().length > 0 && !busy;

  return (
    <Panel
      title="Subscription Folders"
      badge={`${folders.folders.length}`}
      badgeTone="info"
      testId="symbol-subscription-folders"
    >
      {sortedFolders.length === 0 ? (
        <p className="fso-symbol-folders-empty">
          No folders yet. Create one to organize subscribed symbols.
        </p>
      ) : (
        <ul className="fso-symbol-folders-list">
          {sortedFolders.map((folder) => {
            const containsTicker = containingFolderIds.has(folder.id);
            return (
              <li className="fso-symbol-folder-row" key={folder.id}>
                <div>
                  <strong>{folder.name}</strong>
                  <span>
                    {folder.members.length} symbol
                    {folder.members.length === 1 ? "" : "s"}
                  </span>
                </div>
                {subscription.isSubscribed ? (
                  <button
                    type="button"
                    onClick={() =>
                      containsTicker
                        ? onRemoveFromFolder(folder.id)
                        : onAddToFolder(folder.id)
                    }
                    disabled={busy}
                  >
                    {containsTicker ? "Remove" : "Add"}
                  </button>
                ) : null}
                {folder.members.length > 0 ? (
                  <details className="fso-symbol-folder-members">
                    <summary>심볼 목록</summary>
                    <p>{folder.members.map((member) => member.ticker).join(" · ")}</p>
                  </details>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}

      <form
        className="fso-symbol-folder-form"
        onSubmit={(event) => {
          event.preventDefault();
          const nextName = folderName.trim();
          if (!nextName) {
            return;
          }
          onCreateFolder(nextName);
          setFolderName("");
        }}
      >
        <input
          type="text"
          value={folderName}
          maxLength={80}
          placeholder="Folder name"
          onChange={(event) => setFolderName(event.target.value)}
        />
        <button type="submit" disabled={!canCreate}>
          Create
        </button>
      </form>
      {!subscription.isSubscribed ? (
        <p className="fso-symbol-folders-hint">
          Subscribe {normalizedTicker} before assigning it to a folder.
        </p>
      ) : null}
    </Panel>
  );
}
