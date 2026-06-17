"""Central descriptive-only safety scan for the Skill Layer.

Every ``SkillResult`` passes through ``assert_skill_safe`` in the runner, reusing
the single forbidden-wording policy that governs the guard ladder
(``guards.base.find_forbidden_term``) so skills and guards can never diverge on
what counts as buy/sell wording.
"""

from __future__ import annotations

from finskillos.guards.base import find_forbidden_term
from finskillos.skills.base import SkillResult


def assert_skill_safe(result: SkillResult) -> None:
    """Raise ``AssertionError`` if a skill result leaks direct buy/sell advice."""

    blobs: list[str] = [result.title, result.message, *result.watch_next]
    for value in result.evidence.values():
        if isinstance(value, str):
            blobs.append(value)
    term = find_forbidden_term(*blobs)
    if term is not None:
        raise AssertionError(
            f"skill {result.skill_id!r} emitted forbidden term "
            f"{term!r}: {' '.join(blobs)!r}"
        )
