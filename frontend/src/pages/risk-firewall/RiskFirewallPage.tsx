import { useQuery } from "@tanstack/react-query";
import { fetchRiskFirewall } from "@/features/risk-guards/api";
import { ActiveAlertsTable } from "@/features/risk-guards/components/ActiveAlertsTable";
import { GuardResultCard } from "@/features/risk-guards/components/GuardResultCard";
import { RiskProtocolPanel } from "@/features/risk-guards/components/RiskProtocolPanel";
import { riskFirewallFixture } from "@/mocks/fixtures/riskFirewall.fixture";
import {
  Badge,
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  StatusPill,
  WatchpointsPanel,
} from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type {
  GuardStatus,
  RiskFirewallData,
  RiskLevel,
} from "@/features/risk-guards/types";
import "./risk-firewall.css";

export function RiskFirewallPage() {
  const { data, error, failureReason } = useQuery({
    queryKey: ["risk-firewall"],
    queryFn: ({ signal }) => fetchRiskFirewall(signal),
    placeholderData: riskFirewallFixture,
  });
  const liveFailed = Boolean(error ?? failureReason);

  if (error && !data) {
    return (
      <EmptyState
        testId="risk-firewall-error"
        title="Risk Firewall is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? riskFirewallFixture;

  return (
    <div className="fso-risk-firewall" data-testid="risk-firewall-page">
      {liveFailed ? (
        <StatusPill
          label="Live data unavailable — showing sample shape, not live data"
          tone="warning"
          testId="risk-firewall-live-failed"
        />
      ) : null}
      <SectionHeader
        eyebrow="FinSkillOS · Module"
        title="Risk Firewall"
      />
      <div className="fso-v42-topline">
        <JudgmentHeader judgment={payload.judgment} />
        <DriversPanel
          drivers={payload.drivers.map((driver) => ({
            label: driver.title,
            value: driver.score,
            detail: driver.note,
          }))}
        />
        <ConflictsPanel
          conflicts={payload.conflicts.map((conflict) => ({
            label: conflict.title,
            description: conflict.note,
          }))}
        />
      </div>
      <RiskFirewallDataStateBand payload={payload} />
      {/* v3 Phase 8 (183): 2-column layout — the tall guard ladder beside a side
          column that stacks alerts + protocol + interpretation + watchpoints, so
          the right half is used instead of left over as a void. */}
      <div className="fso-risk-firewall-grid">
        <div data-testid="risk-firewall-guard-results">
          <GuardResultCard guards={payload.guards} />
        </div>
        <div className="fso-risk-firewall-side">
          <div data-testid="risk-firewall-active-alerts">
            <ActiveAlertsTable alerts={payload.activeAlerts} />
          </div>
          <div data-testid="risk-firewall-protocol">
            <RiskProtocolPanel
              protocol={payload.protocol}
              safetyCaption={payload.safetyCaption}
            />
          </div>
          <InterpretationPanel
            bullets={[
              payload.interpretation.verdict,
              payload.interpretation.whyItMatters,
              payload.interpretation.whatRemainsUncertain,
            ]}
          />
          <WatchpointsPanel
            watchpoints={payload.watchpoints.map((watchpoint) => ({
              label: watchpoint.title,
              description: watchpoint.note,
            }))}
          />
        </div>
      </div>
      <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
    </div>
  );
}

function RiskFirewallDataStateBand({ payload }: { payload: RiskFirewallData }) {
  const state = payload.dataState;
  const sourceLabel = state.evaluationSource === "live" ? "LIVE" : "FIXTURE";
  const sourceTone: BadgeTone =
    state.evaluationSource === "live" ? "success" : "warning";
  const persistedLabel = state.persistedAlerts ? "PERSISTED" : "READ ONLY";

  return (
    <div
      className="fso-risk-firewall-state-band"
      data-testid="risk-firewall-data-state"
    >
      <RiskFirewallStateItem
        label="Evaluation"
        value={sourceLabel}
        detail={state.sourceNote}
        tone={sourceTone}
      />
      <RiskFirewallStateItem
        label="Risk state"
        value={state.evaluationStatus}
        detail={`${state.highestRiskLevel} highest risk · ${state.flaggedGuardCount} flagged`}
        tone={guardStatusTone(state.evaluationStatus)}
      />
      <RiskFirewallStateItem
        label="Guard ladder"
        value={`${state.guardCount}`}
        detail={`${state.passCount} pass · ${state.alertCount} active alerts`}
        tone={riskLevelTone(state.highestRiskLevel)}
      />
      <RiskFirewallStateItem
        label="Alert writes"
        value={persistedLabel}
        detail={state.reviewNote}
        tone={state.persistedAlerts ? "warning" : "info"}
      />
    </div>
  );
}

function guardStatusTone(status: GuardStatus): BadgeTone {
  if (status === "PASS" || status === "INFO") {
    return "success";
  }
  if (status === "WARN") {
    return "warning";
  }
  return "danger";
}

function riskLevelTone(level: RiskLevel): BadgeTone {
  if (level === "GREEN") {
    return "success";
  }
  if (level === "YELLOW" || level === "ORANGE") {
    return "warning";
  }
  if (level === "RED") {
    return "danger";
  }
  return "neutral";
}

interface RiskFirewallStateItemProps {
  label: string;
  value: string;
  detail: string;
  tone: BadgeTone;
}

function RiskFirewallStateItem({
  label,
  value,
  detail,
  tone,
}: RiskFirewallStateItemProps) {
  return (
    <div className="fso-risk-firewall-state-item">
      <span>{label}</span>
      <Badge tone={tone}>{value}</Badge>
      <small>{detail}</small>
    </div>
  );
}
