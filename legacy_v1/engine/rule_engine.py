"""Applied Skill Rule audit primitives for FinSkillOS.

The structures in this module implement the AUTO-CONTRACT-001 requirement from
`FinSkillOS_skills/skills/05_vibecoding_automation.md`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


RULE_PREFIX_MEANINGS = {
    "DATA": "데이터 구조 이해 및 품질 검사",
    "SCHEMA": "표준 스키마 매핑",
    "METRIC": "금융 지표 계산",
    "VIS": "시각화 선택",
    "DASH": "대시보드 레이아웃 구성",
    "INSIGHT": "인사이트 생성",
    "RISK": "리스크 분류",
    "SAFE": "금융 표현 안전장치",
    "AUTO": "바이브코딩 및 자동 생성",
    "EXT": "확장 기능 아이디어",
}


@dataclass(frozen=True)
class AppliedRule:
    """A single Skill Rule application record shown in dashboard audit logs."""

    rule_id: str
    step: str
    condition: str
    action: str
    result: str
    severity: str = "INFO"

    @property
    def prefix(self) -> str:
        return self.rule_id.split("-", 1)[0]

    @property
    def category(self) -> str:
        return RULE_PREFIX_MEANINGS.get(self.prefix, "기타")

    def to_dict(self) -> dict[str, str]:
        record = asdict(self)
        record["prefix"] = self.prefix
        record["category"] = self.category
        return record


class RuleAuditLog:
    """Collects applied Skill Rules across the analysis pipeline."""

    def __init__(self, rules: Iterable[AppliedRule] | None = None) -> None:
        self._rules: list[AppliedRule] = []
        if rules:
            self.extend(rules)

    def add(
        self,
        rule_id: str,
        step: str,
        condition: str,
        action: str,
        result: str,
        severity: str = "INFO",
    ) -> AppliedRule:
        rule = AppliedRule(
            rule_id=rule_id,
            step=step,
            condition=condition,
            action=action,
            result=result,
            severity=severity,
        )
        self._rules.append(rule)
        return rule

    def extend(self, rules: Iterable[AppliedRule | dict[str, str]]) -> None:
        for rule in rules:
            if isinstance(rule, AppliedRule):
                self._rules.append(rule)
            else:
                payload = {
                    key: rule[key]
                    for key in ("rule_id", "step", "condition", "action", "result", "severity")
                    if key in rule
                }
                self._rules.append(AppliedRule(**payload))

    def to_records(self) -> list[dict[str, str | int]]:
        return [
            {"order": index, **rule.to_dict()}
            for index, rule in enumerate(self._rules, start=1)
        ]

    def deduplicated_records(self) -> list[dict[str, str | int]]:
        seen: set[tuple[str, str, str]] = set()
        records: list[dict[str, str | int]] = []
        for rule in self._rules:
            key = (rule.rule_id, rule.step, rule.result)
            if key in seen:
                continue
            seen.add(key)
            records.append({"order": len(records) + 1, **rule.to_dict()})
        return records

    def summary_by_prefix(self, deduplicated: bool = True) -> list[dict[str, str | int]]:
        records = self.deduplicated_records() if deduplicated else self.to_records()
        counts: dict[str, dict[str, str | int]] = {}
        for record in records:
            prefix = str(record["prefix"])
            if prefix not in counts:
                counts[prefix] = {
                    "prefix": prefix,
                    "category": str(record["category"]),
                    "count": 0,
                }
            counts[prefix]["count"] = int(counts[prefix]["count"]) + 1
        return sorted(counts.values(), key=lambda item: str(item["prefix"]))

    def has_prefixes(self, prefixes: Iterable[str], deduplicated: bool = True) -> dict[str, bool]:
        records = self.deduplicated_records() if deduplicated else self.to_records()
        present = {str(record["prefix"]) for record in records}
        return {prefix: prefix in present for prefix in prefixes}

    def __len__(self) -> int:
        return len(self._rules)
