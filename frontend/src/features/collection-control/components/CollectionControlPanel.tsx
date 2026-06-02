import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addFolderSymbol,
  createFolder,
  deleteFolder,
  fetchCollectionControl,
  globalToggle,
  patchFolderFlags,
  removeFolderSymbol,
} from "../api";
import type {
  CollectionControlData,
  CollectionFlag,
  CollectionFlagPatch,
  CollectionFolder,
} from "../types";
import { collectionControlFixture } from "@/mocks/fixtures/collectionControl.fixture";
import { SafetyCaption, SectionHeader, StatusPill } from "@/shared/ui";

const QUERY_KEY = ["collection-control"];

const FLAG_COLUMNS: { flag: CollectionFlag; label: string; patchKey: keyof CollectionFlagPatch }[] = [
  { flag: "is_active", label: "Active", patchKey: "isActive" },
  { flag: "track_market", label: "Price", patchKey: "trackMarket" },
  { flag: "track_indicators", label: "Indicators", patchKey: "trackIndicators" },
  { flag: "track_news", label: "News", patchKey: "trackNews" },
];

export function CollectionControlPanel(): JSX.Element {
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<{ tone: "success" | "error" | "info"; text: string } | null>(
    null,
  );
  const [newFolder, setNewFolder] = useState("");
  const [symbolDraft, setSymbolDraft] = useState<Record<string, string>>({});

  const { data, isLoading, isError } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: ({ signal }) => fetchCollectionControl(signal),
    placeholderData: collectionControlFixture,
  });
  const payload = data ?? collectionControlFixture;

  const applyResult = (result: CollectionControlData): void => {
    queryClient.setQueryData(QUERY_KEY, result);
  };

  const mutation = useMutation({
    mutationFn: (input: { action: () => Promise<CollectionControlData>; message: string }) =>
      input.action(),
    onSuccess: (result, input) => {
      applyResult(result);
      setNotice({ tone: "success", text: input.message });
    },
    onError: (error) => {
      setNotice({
        tone: "error",
        text: error instanceof Error ? error.message : "Action failed.",
      });
    },
  });

  const run = (action: () => Promise<CollectionControlData>, message: string): void => {
    mutation.mutate({ action, message });
  };

  const onToggleFlag = (folder: CollectionFolder, column: (typeof FLAG_COLUMNS)[number]): void => {
    const current = folderFlagValue(folder, column.patchKey);
    run(
      () => patchFolderFlags(folder.id, { [column.patchKey]: !current }),
      `${folder.name}: ${column.label} ${!current ? "on" : "off"}.`,
    );
  };

  const onGlobalToggle = (flag: CollectionFlag, value: boolean): void => {
    run(() => globalToggle(flag, value), `All folders: ${flagLabel(flag)} ${value ? "on" : "off"}.`);
  };

  const onCreateFolder = (): void => {
    const name = newFolder.trim();
    if (!name) return;
    setNewFolder("");
    run(() => createFolder(name), `Folder "${name}" created.`);
  };

  const onDeleteFolder = (folder: CollectionFolder): void => {
    run(() => deleteFolder(folder.id), `Folder "${folder.name}" removed.`);
  };

  const onAddSymbol = (folder: CollectionFolder): void => {
    const ticker = (symbolDraft[folder.id] ?? "").trim().toUpperCase();
    if (!ticker) return;
    setSymbolDraft((prev) => ({ ...prev, [folder.id]: "" }));
    run(() => addFolderSymbol(folder.id, ticker), `${ticker} added to ${folder.name}.`);
  };

  const onRemoveSymbol = (folder: CollectionFolder, ticker: string): void => {
    run(() => removeFolderSymbol(folder.id, ticker), `${ticker} removed from ${folder.name}.`);
  };

  const totals = payload.totals;
  const folders = payload.folders;
  const busy = mutation.isPending;

  const globalState = useMemo(
    () => ({
      is_active: totals.allActive,
      track_market: totals.marketAll,
      track_indicators: totals.indicatorsAll,
      track_news: totals.newsAll,
    }),
    [totals],
  );

  return (
    <div className="fso-collection" data-testid="collection-control-panel">
      <SectionHeader eyebrow="Folder-driven" title="Collection Control" />
      <p className="fso-collection-subtitle">
        Decide which symbols the worker observes. Add tickers to a folder and toggle
        Price / Indicators / News per folder or globally.
      </p>

      {isError ? (
        <StatusPill
          label="Live data unavailable — showing sample shape, not live data"
          tone="warning"
          testId="collection-control-live-failed"
        />
      ) : null}

      <div className="fso-collection-totals" data-testid="collection-control-totals">
        <CoverageStat label="Folders" value={`${totals.activeFolderCount}/${totals.folderCount} active`} />
        <CoverageStat label="Price" value={`${totals.marketTickerCount} symbols`} />
        <CoverageStat label="Indicators" value={`${totals.indicatorTickerCount} symbols`} />
        <CoverageStat label="News" value={`${totals.newsTickerCount} symbols`} />
      </div>

      <div className="fso-collection-globals" role="group" aria-label="Global collection toggles">
        <span className="fso-collection-globals-label">All folders</span>
        {FLAG_COLUMNS.map((column) => (
          <label key={column.flag} className="fso-collection-check">
            <input
              type="checkbox"
              checked={globalState[column.flag]}
              disabled={busy || folders.length === 0}
              data-testid={`collection-global-${column.flag}`}
              onChange={(event) => onGlobalToggle(column.flag, event.target.checked)}
            />
            <span>{column.label}</span>
          </label>
        ))}
      </div>

      <form
        className="fso-collection-newfolder"
        onSubmit={(event) => {
          event.preventDefault();
          onCreateFolder();
        }}
      >
        <input
          type="text"
          value={newFolder}
          placeholder="New folder name"
          aria-label="New folder name"
          maxLength={80}
          data-testid="collection-new-folder-input"
          onChange={(event) => setNewFolder(event.target.value)}
        />
        <button type="submit" disabled={busy || !newFolder.trim()} data-testid="collection-create-folder">
          Create folder
        </button>
      </form>

      {notice ? (
        <p
          className="fso-collection-notice"
          data-tone={notice.tone}
          data-testid="collection-control-notice"
          role="status"
        >
          {notice.text}
        </p>
      ) : null}

      <div className="fso-collection-folders">
        {isLoading && folders.length === 0 ? (
          <p className="fso-collection-empty">Loading folders…</p>
        ) : folders.length === 0 ? (
          <p className="fso-collection-empty" data-testid="collection-control-empty">
            No folders yet. Create one above, then add tickers to start tracking them.
          </p>
        ) : (
          folders.map((folder) => (
            <FolderCard
              key={folder.id}
              folder={folder}
              busy={busy}
              symbolDraft={symbolDraft[folder.id] ?? ""}
              onSymbolDraftChange={(value) =>
                setSymbolDraft((prev) => ({ ...prev, [folder.id]: value }))
              }
              onToggleFlag={(column) => onToggleFlag(folder, column)}
              onAddSymbol={() => onAddSymbol(folder)}
              onRemoveSymbol={(ticker) => onRemoveSymbol(folder, ticker)}
              onDeleteFolder={() => onDeleteFolder(folder)}
            />
          ))
        )}
      </div>

      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}

function FolderCard({
  folder,
  busy,
  symbolDraft,
  onSymbolDraftChange,
  onToggleFlag,
  onAddSymbol,
  onRemoveSymbol,
  onDeleteFolder,
}: {
  folder: CollectionFolder;
  busy: boolean;
  symbolDraft: string;
  onSymbolDraftChange: (value: string) => void;
  onToggleFlag: (column: (typeof FLAG_COLUMNS)[number]) => void;
  onAddSymbol: () => void;
  onRemoveSymbol: (ticker: string) => void;
  onDeleteFolder: () => void;
}): JSX.Element {
  const inactive = !folder.isActive;
  const allTypesOff = !folder.trackMarket && !folder.trackIndicators && !folder.trackNews;
  return (
    <section
      className={`fso-collection-card${inactive ? " is-inactive" : ""}`}
      data-testid={`collection-folder-${folder.id}`}
      data-folder-name={folder.name}
    >
      <header className="fso-collection-card-head">
        <div className="fso-collection-card-title">
          <h3>{folder.name}</h3>
          {folder.isSystem ? <span className="fso-collection-system-badge">System</span> : null}
          <span className="fso-collection-count">{folder.memberCount} symbols</span>
        </div>
        <button
          type="button"
          className="fso-collection-delete"
          disabled={busy || folder.isSystem}
          title={folder.isSystem ? "The System folder is protected." : "Delete folder"}
          data-testid={`collection-delete-${folder.id}`}
          onClick={onDeleteFolder}
        >
          Delete
        </button>
      </header>

      {folder.description ? (
        <p className="fso-collection-card-desc">{folder.description}</p>
      ) : null}

      <div className="fso-collection-flags" role="group" aria-label={`${folder.name} collection types`}>
        {FLAG_COLUMNS.map((column) => (
          <label key={column.flag} className="fso-collection-check">
            <input
              type="checkbox"
              checked={folderFlagValue(folder, column.patchKey)}
              disabled={busy}
              data-testid={`collection-flag-${folder.id}-${column.flag}`}
              onChange={() => onToggleFlag(column)}
            />
            <span>{column.label}</span>
          </label>
        ))}
      </div>

      {inactive ? (
        <p className="fso-collection-warn" data-testid={`collection-inactive-${folder.id}`}>
          Inactive — none of these symbols are collected.
        </p>
      ) : allTypesOff ? (
        <p className="fso-collection-warn">Active, but every collection type is off.</p>
      ) : null}

      <div className="fso-collection-members">
        {folder.members.length === 0 ? (
          <span className="fso-collection-empty-chip">No symbols yet.</span>
        ) : (
          folder.members.map((member) => (
            <span key={member.ticker} className="fso-collection-chip">
              {member.ticker}
              <button
                type="button"
                aria-label={`Remove ${member.ticker} from ${folder.name}`}
                disabled={busy}
                data-testid={`collection-remove-${folder.id}-${member.ticker}`}
                onClick={() => onRemoveSymbol(member.ticker)}
              >
                ×
              </button>
            </span>
          ))
        )}
      </div>

      <form
        className="fso-collection-addsymbol"
        onSubmit={(event) => {
          event.preventDefault();
          onAddSymbol();
        }}
      >
        <input
          type="text"
          value={symbolDraft}
          placeholder="Add ticker (e.g. NVDA)"
          aria-label={`Add ticker to ${folder.name}`}
          maxLength={20}
          data-testid={`collection-add-input-${folder.id}`}
          onChange={(event) => onSymbolDraftChange(event.target.value)}
        />
        <button type="submit" disabled={busy || !symbolDraft.trim()} data-testid={`collection-add-${folder.id}`}>
          Add
        </button>
      </form>
    </section>
  );
}

function CoverageStat({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="fso-collection-stat">
      <span className="fso-collection-stat-label">{label}</span>
      <span className="fso-collection-stat-value">{value}</span>
    </div>
  );
}

function folderFlagValue(folder: CollectionFolder, key: keyof CollectionFlagPatch): boolean {
  switch (key) {
    case "isActive":
      return folder.isActive;
    case "trackMarket":
      return folder.trackMarket;
    case "trackIndicators":
      return folder.trackIndicators;
    case "trackNews":
      return folder.trackNews;
    default:
      return false;
  }
}

function flagLabel(flag: CollectionFlag): string {
  return FLAG_COLUMNS.find((column) => column.flag === flag)?.label ?? flag;
}
