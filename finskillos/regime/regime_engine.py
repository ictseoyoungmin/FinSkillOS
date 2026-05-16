from dataclasses import dataclass


@dataclass(frozen=True)
class RegimeInput:
    vix: float
    index_above_200d: bool
    rsi: float


@dataclass(frozen=True)
class RegimeDecision:
    regime: str
    decision_mode: str
    reason: str


def classify_regime(signal: RegimeInput) -> RegimeDecision:
    if signal.vix >= 30 or not signal.index_above_200d:
        return RegimeDecision("RISK_OFF", "PROTECT", "Stress signal is elevated.")
    if signal.rsi >= 75:
        return RegimeDecision("RISK_ON_OVERHEAT", "WAIT", "Momentum is extended.")
    return RegimeDecision("RISK_ON", "NORMAL", "No major stress signal is active.")
