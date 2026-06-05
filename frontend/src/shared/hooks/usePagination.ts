import { useEffect, useMemo, useState } from "react";

/**
 * Client-side pagination for a long list (v3 Phase 8 / Slice 185). Returns the
 * visible page slice + controls; resets to page 0 when the list size changes.
 */
export function usePagination<T>(items: T[], pageSize: number) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));

  useEffect(() => {
    setPage(0);
  }, [items.length, pageSize]);

  const clamped = Math.min(page, pageCount - 1);
  const visible = useMemo(
    () => items.slice(clamped * pageSize, clamped * pageSize + pageSize),
    [items, clamped, pageSize],
  );

  return {
    page: clamped,
    pageCount,
    visible,
    setPage,
    prev: () => setPage((p) => Math.max(0, p - 1)),
    next: () => setPage((p) => Math.min(pageCount - 1, p + 1)),
  };
}
