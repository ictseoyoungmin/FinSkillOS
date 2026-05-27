import type { CSSProperties } from "react";
import type { NewsTickerIdentity } from "../types";
import "./ticker-logo-mark.css";

export interface TickerLogoMarkProps {
  identity: NewsTickerIdentity;
}

export function TickerLogoMark({ identity }: TickerLogoMarkProps) {
  if (identity.logoUrl) {
    return (
      <img
        alt={`${identity.name} logo`}
        className="fso-news-ticker-logo"
        src={identity.logoUrl}
      />
    );
  }

  return (
    <span
      className="fso-news-ticker-avatar"
      style={{ "--ticker-color": identity.brandColor } as CSSProperties}
    >
      {identity.avatarText}
    </span>
  );
}
