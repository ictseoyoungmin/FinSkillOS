import { Badge, Panel } from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { EvidenceGraph } from "../types";
import "./evidence-graph-panel.css";

export interface EvidenceGraphPanelProps {
  graph: EvidenceGraph;
}

const NODE_LABELS: Record<string, string> = {
  regime: "Regime",
  risk: "Risk Firewall",
  events: "Catalyst Watch",
  portfolio: "Portfolio",
};

/**
 * Cross-tab evidence graph (Slice 167). Renders the regime / risk / events /
 * portfolio nodes and their descriptive cross-references as a node grid + link
 * list. Read-only interpretation — no execution controls.
 */
export function EvidenceGraphPanel({ graph }: EvidenceGraphPanelProps) {
  if (graph.nodes.length === 0) {
    return null;
  }
  return (
    <Panel
      title="Evidence Graph"
      badge={`${graph.nodes.length} nodes · ${graph.links.length} links`}
      badgeTone="info"
      testId="evidence-graph"
    >
      <p className="fso-evidence-graph-summary">{graph.summary}</p>
      <div className="fso-evidence-graph-nodes">
        {graph.nodes.map((node) => (
          <article
            key={node.key}
            className="fso-evidence-node"
            data-tone={node.tone}
            data-testid={`evidence-node-${node.key}`}
          >
            <div className="fso-evidence-node-head">
              <span>{node.label}</span>
              <Badge tone={node.tone as BadgeTone}>{node.state}</Badge>
            </div>
            {node.drivers.length > 0 ? (
              <ul>
                {node.drivers.map((driver) => (
                  <li key={driver}>{driver}</li>
                ))}
              </ul>
            ) : null}
          </article>
        ))}
      </div>
      {graph.links.length > 0 ? (
        <ul className="fso-evidence-graph-links" data-testid="evidence-graph-links">
          {graph.links.map((link) => (
            <li key={`${link.source}-${link.target}-${link.relation}`}>
              <span className="fso-evidence-link-path">
                {NODE_LABELS[link.source] ?? link.source} →{" "}
                {NODE_LABELS[link.target] ?? link.target}
              </span>
              <span className="fso-evidence-link-relation">{link.relation}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </Panel>
  );
}
