import { useState, type FormEvent } from "react";
import "./ticker-search.css";

export interface TickerSearchOption {
  symbol: string;
  label: string;
}

export interface TickerSearchProps {
  initialValue: string;
  placeholder?: string;
  suggestions?: TickerSearchOption[];
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
  suggestions = [],
  onSubmit,
}: TickerSearchProps) {
  const [value, setValue] = useState<string>(initialValue);
  const listId = suggestions.length > 0 ? "ticker-search-options" : undefined;

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
        list={listId}
        aria-label="Ticker search"
      />
      {suggestions.length > 0 ? (
        <datalist id="ticker-search-options">
          {suggestions.map((option) => (
            <option
              key={option.symbol}
              value={option.symbol}
              label={option.label}
            />
          ))}
        </datalist>
      ) : null}
      <button
        type="submit"
        className="fso-ticker-search-submit"
        data-testid="ticker-search-submit"
      >
        Load
      </button>
      {suggestions.length > 0 ? (
        <div className="fso-ticker-search-options" aria-label="Stored symbol shortcuts">
          {suggestions.map((option) => (
            <button
              key={option.symbol}
              type="button"
              className="fso-ticker-search-option"
              onClick={() => {
                setValue(option.symbol);
                onSubmit(option.symbol);
              }}
              title={option.label}
            >
              {option.symbol}
            </button>
          ))}
        </div>
      ) : null}
    </form>
  );
}
