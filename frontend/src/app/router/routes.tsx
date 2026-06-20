import { Navigate, Route, Routes } from "react-router-dom";
import { ControlRoomPage } from "@/pages/control-room/ControlRoomPage";
import { MarketKernelPage } from "@/pages/market-kernel/MarketKernelPage";
import { AnalysisWorkspacePage } from "@/pages/analysis-workspace/AnalysisWorkspacePage";
import { SymbolLabPage } from "@/pages/symbol-lab/SymbolLabPage";
import { RiskFirewallPage } from "@/pages/risk-firewall/RiskFirewallPage";
import { MissionControlPage } from "@/pages/mission-control/MissionControlPage";
import { NewsIntelligencePage } from "@/pages/news-intelligence/NewsIntelligencePage";
import { CatalystWatchPage } from "@/pages/catalyst-watch/CatalystWatchPage";
import { TradeMemoryPage } from "@/pages/trade-memory/TradeMemoryPage";
import { QuantLabPage } from "@/pages/quant-lab/QuantLabPage";
import { SystemOpsPage } from "@/pages/system-ops/SystemOpsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ControlRoomPage />} />
      <Route path="/market-kernel" element={<MarketKernelPage />} />
      <Route
        path="/analysis-workspace"
        element={<AnalysisWorkspacePage />}
      />
      <Route path="/symbol-lab" element={<SymbolLabPage />} />
      <Route path="/risk-firewall" element={<RiskFirewallPage />} />
      <Route path="/mission-control" element={<MissionControlPage />} />
      <Route path="/news-intel" element={<NewsIntelligencePage />} />
      <Route path="/catalyst-watch" element={<CatalystWatchPage />} />
      <Route path="/trade-memory" element={<TradeMemoryPage />} />
      <Route path="/quant-lab" element={<QuantLabPage />} />
      <Route path="/system-ops" element={<SystemOpsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
