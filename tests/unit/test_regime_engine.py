from finskillos.regime.regime_engine import RegimeInput, classify_regime


def test_regime_engine_protects_when_vix_is_elevated() -> None:
    decision = classify_regime(RegimeInput(vix=32, index_above_200d=True, rsi=50))

    assert decision.regime == "RISK_OFF"
    assert decision.decision_mode == "PROTECT"


def test_regime_engine_waits_when_market_is_overheated() -> None:
    decision = classify_regime(RegimeInput(vix=18, index_above_200d=True, rsi=78))

    assert decision.regime == "RISK_ON_OVERHEAT"
    assert decision.decision_mode == "WAIT"


def test_regime_engine_allows_normal_mode_for_stable_inputs() -> None:
    decision = classify_regime(RegimeInput(vix=16, index_above_200d=True, rsi=55))

    assert decision.regime == "RISK_ON"
    assert decision.decision_mode == "NORMAL"
