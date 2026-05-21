import { useState, type FormEvent } from "react";
import "./ticker-search.css";

export interface TickerSearchProps {
  initialValue: string;
  placeholder?: string;
  onSubmit: (value: string) => void;
}

/**
 * Free-text ticker input. Normalises input the same way the Python
 * helper `finskillos.ui.view_models.symbol_lab_vm.normalize_ticker`
 * does (strip + uppercase) so the API receives matching keys.
 */
export function TickerSearch({
  initialValue,
  placeholder = "Search ticker (e.g. NVDA, TSLA, AAPL)",
  onSubmit,
}: TickerSearchProps) {
  const [value, setValue] = useState<string>(initialValue);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const normalised = value.trim().toUpperCase();
    if (!normalised) return;
    onSubmit(normalised);
  };

  return (
    <form
      onSubmit={submit}
      className="fso-ticker-search"
      data-testid="ticker-search"
    >
      <label htmlFor="ticker-search-input" className="fso-ticker-search-label">
        Ticker
      </label>
      <input
        id="ticker-search-input"
        type="text"
        className="fso-ticker-search-input"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        aria-label="Ticker search"
      />
      <button
        type="submit"
        className="fso-ticker-search-submit"
        data-testid="ticker-search-submit"
      >
        Load
      </button>
    </form>
  );
}
