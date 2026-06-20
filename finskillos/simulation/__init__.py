"""FinSkillOS Quant Simulation Lab (Phase 21).

Descriptive strategy simulation over stored historical bars — research only, never
real trading. See ``docs/v4/PHASE_21_Quant_Sim_Lab.md``.
"""

from finskillos.simulation.conditions import All, Any, Compare, Condition, Cross
from finskillos.simulation.engine import (
    SIMULATION_CAPTION,
    Bar,
    EquityPoint,
    SimulationResult,
    StrategySpec,
    simulate,
)
from finskillos.simulation.metrics import SimMetrics

__all__ = [
    "SIMULATION_CAPTION",
    "All",
    "Any",
    "Bar",
    "Compare",
    "Condition",
    "Cross",
    "EquityPoint",
    "SimMetrics",
    "SimulationResult",
    "StrategySpec",
    "simulate",
]
