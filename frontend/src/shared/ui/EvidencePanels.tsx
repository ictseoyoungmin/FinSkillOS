import { Panel } from "./Panel";
import "./evidence-panels.css";

export type EvidenceTone =
  | "info"
  | "warning"
  | "danger"
  | "neutral"
  | "success";

export interface DriverRow {
  label: string;
  value: string;
  detail?: string;
}

export interface ConflictRow {
  label: string;
  description: string;
  tone?: EvidenceTone;
}

/** Drivers panel — value + supporting detail per row. */
export function DriversPanel({
  title = "Primary Drivers",
  drivers,
  testId = "drivers-panel",
}: {
  title?: string;
  drivers: DriverRow[];
  testId?: string;
}) {
  return (
    <Panel
      title={title}
      badge={`${drivers.length}`}
      badgeTone="info"
      testId={testId}
    >
      <dl className="fso-drivers-list">
        {drivers.map((driver) => (
          <div key={driver.label} className="fso-drivers-row">
            <dt>{driver.label}</dt>
            <dd>
              <span className="fso-drivers-value">{driver.value}</span>
              {driver.detail ? (
                <span className="fso-drivers-detail">{driver.detail}</span>
              ) : null}
            </dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}

/** Conflicts / Uncertainty panel. */
export function ConflictsPanel({
  conflicts,
  testId = "conflicts-panel",
}: {
  conflicts: ConflictRow[];
  testId?: string;
}) {
  return (
    <Panel
      title="Conflicts / Uncertainty"
      badge={`${conflicts.length}`}
      badgeTone="warning"
      testId={testId}
    >
      <ul className="fso-conflicts-list">
        {conflicts.map((entry) => (
          <li
            key={entry.label}
            className={`fso-conflicts-row fso-tone-${entry.tone ?? "warning"}`}
          >
            <div className="fso-conflicts-label">{entry.label}</div>
            <p className="fso-conflicts-desc">{entry.description}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}

/** Integrated Interpretation panel — bulleted descriptive paragraphs. */
export function InterpretationPanel({
  bullets,
  testId = "interpretation-panel",
}: {
  bullets: string[];
  testId?: string;
}) {
  return (
    <Panel
      title="Integrated Interpretation"
      badge={`${bullets.length}`}
      badgeTone="info"
      testId={testId}
    >
      <ul className="fso-interpretation-list">
        {bullets.map((bullet, index) => (
          <li key={index}>{bullet}</li>
        ))}
      </ul>
    </Panel>
  );
}

/** Watchpoints / Review-conditions panel. */
export function WatchpointsPanel({
  watchpoints,
  title = "Watchpoints",
  testId = "watchpoints-panel",
}: {
  watchpoints: ConflictRow[];
  title?: string;
  testId?: string;
}) {
  return (
    <Panel
      title={title}
      badge={`${watchpoints.length}`}
      badgeTone="info"
      testId={testId}
    >
      <ul className="fso-watchpoints-list">
        {watchpoints.map((entry) => (
          <li
            key={entry.label}
            className={`fso-watchpoints-row fso-tone-${entry.tone ?? "info"}`}
          >
            <div className="fso-watchpoints-label">{entry.label}</div>
            <p className="fso-watchpoints-desc">{entry.description}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
