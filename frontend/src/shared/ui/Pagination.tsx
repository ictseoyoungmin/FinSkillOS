import "./pagination.css";

export interface PaginationProps {
  page: number;
  pageCount: number;
  onPrev: () => void;
  onNext: () => void;
  label?: string;
  testId?: string;
}

/**
 * Shared prev / next pager (v3 Phase 8 / Slice 185). Renders nothing for a
 * single page so callers can drop it in unconditionally.
 */
export function Pagination({
  page,
  pageCount,
  onPrev,
  onNext,
  label = "Pagination",
  testId,
}: PaginationProps) {
  if (pageCount <= 1) {
    return null;
  }
  return (
    <div className="fso-pagination" aria-label={label} data-testid={testId}>
      <button type="button" onClick={onPrev} disabled={page === 0}>
        Prev
      </button>
      <span>
        {page + 1} / {pageCount}
      </span>
      <button
        type="button"
        onClick={onNext}
        disabled={page >= pageCount - 1}
      >
        Next
      </button>
    </div>
  );
}
