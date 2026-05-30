# Tab Review & Backlog — Refactor / Hardening · Feature · UI·UX

Updated: 2026-05-30 (after Slice 83)

이 문서는 v4.2 cockpit 10개 탭을 **리팩토링/하드닝 · 기능 추가/개선 · UI/UX 개선**
세 축으로 검토한 백로그다. 슬라이스 진행 상태는 `.devmd/CURRENT_STATE.md`가
권위이며, 여기 항목은 그 위에서 "다음에 할 수 있는 것"을 근거와 함께 정리한 것이다.
아직 구현 지시가 아니며, 각 항목은 독립 슬라이스로 쪼갤 수 있다.

## 범례

- 우선순위: **P1** (정합성/신뢰성에 직접 영향) · **P2** (가치 높은 개선) · **P3** (있으면 좋음)
- 작업량: **S** (1슬라이스 이하) · **M** (1~2슬라이스) · **L** (여러 슬라이스/설계 필요)
- 모든 신규 출력은 descriptive-only 규약(매수/매도·실행 표현 금지) 준수.

---

## 0. Cross-Cutting (탭 공통)

### 리팩토링 / 하드닝
- **공유 `api/timeutil.py` 추출** — `_as_utc`(4개 라우트) / `_iso`(6개 라우트)가
  파일마다 복붙돼 있다. `api/coverage.py`(Slice 83)·`mark_db_unavailable`(Slice 82)
  처럼 단일 모듈로 통합. (P2 / S)
- **live-empty / live-error 빌더 공통화** — Slice 80에서 라우트별 `_empty_live_response`
  /`_error_live_response`가 4개 라우트에 중복 생성됐다. 공통 시그니처
  (`source="live"`, `db="LIVE"`, 예외 클래스명만, fixture 스캐폴드 재사용)를
  헬퍼/팩토리로 묶어 새 라우트가 같은 계약을 쉽게 따르게. (P2 / M)
- **`get_session_scope` 의 에러 구분** — `api/dependencies.py:27` TODO. 현재
  `except Exception: yield None` 이 "DB 미설정"과 "DB 연결 실패/쿼리 오류"를 모두
  `None`으로 뭉갠다. 후자는 503/구조화 JSON로 surface하고 전자만 fixture로
  떨어지게 분리하면 Slice 80/82의 정직성 방향이 완성된다. (P1 / M)
- **fixture-scaffold-then-overwrite 패턴 명문화/대체** — 8개 라우트가
  `payload = X_fixture()` 로 시작해 필드를 덮어쓴다. 빠르지만 "잊고 안 덮은 필드가
  fixture값으로 샌다"는 위험. 라우트별 명시적 builder로 점진 대체하거나 최소한
  "live에서 반드시 덮어야 하는 필드" 계약 테스트를 추가. (P2 / M)
- **Docker 풀스위트의 env-state 실패 정리** — Slice 81이 v4.2 contract를 고쳤고
  Slice 83이 market_kernel `trendState` 테스트를 고쳤다. 같은 "no-header 호출이
  seeded DB에서 live를 받아 fixture 기대값과 어긋남" 부류가 다른 테스트 파일에도
  남아있을 수 있다(예: `test_seed_sample_events...`는 별개의 영속-DB seed 이슈).
  전 테스트를 한 번 audit해 fixture-pin 또는 결정적 seed로 정리. (P1 / M)

### UI/UX (공통)
- **silent fallback → explicit failure pill** — `frontend/src/features/market/api.ts:14`,
  `features/analysis/api.ts:12` TODO. 네트워크/DB 실패 시 조용히 fixture로 떨어지지
  말고 "라이브 실패" 칩을 노출(백엔드는 이미 Slice 80에서 live-error를 줌). (P1 / S)
- **로딩/에러/빈 상태 일관성** — 탭마다 `placeholderData`(fixture) 또는
  `isPlaceholderData` 처리 방식이 제각각. 공통 `LiveStateBanner`(live/fixture/
  db-unavailable/error) 컴포넌트로 통일. (P2 / M)
- **접근성** — pure-SVG 차트(market-tape, candle, line)에 `role`/`aria-label`/표
  대체 텍스트, 상태 칩에 의미 라벨, command palette 외 키보드 포커스 순서 점검. (P2 / M)
- **Dead code 제거** — `frontend/src/pages/PlaceholderPage.tsx`는 라우터에서
  더 이상 참조되지 않음(전 탭 실제 페이지). 삭제. (P3 / S)
- **오프라인 최소 콘텐츠 상태** — Slice 82는 `db="MISSING"` 라벨만 붙였고 본문은
  여전히 seeded fixture 숫자를 보여준다. "DB를 연결하세요" 식 최소 콘텐츠 상태로
  대체하면 "샘플과 혼동 금지" 의도가 더 강해짐. (P2 / M, Slice 82 후속)

---

## 1. Control Room (`/`)

현황: DB-backed operating overview(Slice 66/69), 레일별 freshness 상세·STALE/FRESH/
MISSING 분류(72/75), staleness 임계값 settings 계약(78), normalized market-tape SVG.

- **리팩토링/하드닝**: 비-승격 레일을 `dataState`에서 partial로 표시 중 —
  market/catalyst/watchlist 외 레일까지 완전 live 합성으로 승격. 공유 freshness
  헬퍼는 timeutil 추출에 포함. (P2 / M)
- **기능**: "직전 스냅샷 대비 무엇이 변했나" 요약(레짐 전환/신규 알림/신규 catalyst)
  한 줄. freshness 임계값을 운영자 노트/System Ops 데이터소스 칩에 노출(Next Useful #2). (P2 / M)
- **UI/UX**: market-tape SVG에 hover 값 툴팁 + 접근성 라벨. state band 정보 밀도
  조정(현재 칩 다수). (P3 / S)

## 2. Market Kernel (`/market-kernel`)

현황: DB read model(24), coverage 어휘 공유(74/83), candle/indicator/event 패널,
`dataState`(59).

- **리팩토링/하드닝**: provider 경계는 page-render 중 호출 안 함(OK). `_iso`/`_as_utc`
  timeutil 통합. (P2 / S)
- **기능**: **event overlay 라이브화** — EMPTY 경로에서 `event_overlay_status`가
  하드코딩 "MISSING". Catalyst Watch 이벤트를 캔들 위에 실제 오버레이. Symbol Lab처럼
  **다중 timeframe** 쿼리 도입. (P2 / M)
- **UI/UX**: `market/api.ts` silent fallback → 실패 칩(공통 항목). 캔들 crosshair/툴팁. (P2 / S)

## 3. Analysis Workspace (`/analysis-workspace`)

현황: Index Lab DB read model(65), coverage levels·ranked-tape readiness·missing-row
preview(68), state band(62).

- **리팩토링/하드닝**: `features/analysis/api.ts:12`의 13.6 cleanup §7 TODO 정리
  (error-surface 계약). (P1 / S)
- **기능**: 섹터/브레드스 heatmap, 강·약 로테이션 추세(현재 강3/약3 카드). (P3 / M)
- **UI/UX**: missing-row preview·coverage band 렌더 밀도, universe 테이블 정렬/필터. (P3 / S)

## 4. Symbol Lab (`/symbol-lab`)

현황: 가장 성숙. DB read model(27), 임의 심볼 검색·preview(13.12/29), OHLC 캔들+
EMA/Bollinger 오버레이·timeframe·yfinance(31), logo 캐시(35), 구독 폴더(34),
coverage 공유(74/83), `dataState`(56).

- **리팩토링/하드닝**: provider preview 재검증(stale mock tail) 동작 유지. yfinance
  경계 hardening(타임아웃/에러 카피)은 공통 live-error 패턴에 흡수. (P2 / S)
- **기능**: 임의 심볼에도 alert/포지션 컨텍스트 확장, **두 심볼 비교 오버레이**,
  검색 결과에서 바로 watchlist/folder 추가. (P2 / M)
- **UI/UX**: 캔들 crosshair·툴팁, recent-bars 테이블·news 패널 밀도, 로고 fallback
  아바타 일관성. (P3 / S)

## 5. Risk Firewall (`/risk-firewall`)

현황: DB read model(21), guard evidence density(60), `dataState`, live-empty/error(80).

- **리팩토링/하드닝**: **`EVENT_PLACEHOLDER_GUARD` 실연결** — fixture에 여전히
  Event Placeholder 가드(Slice 06 이래 placeholder). Catalyst Watch 라이브 이벤트
  노출도로 event-risk 가드를 실제 평가에 연결. (P1 / M)
- **기능**: 가드 임계값(cash/concentration/drawdown 등)을 settings 계약으로
  (Control Room freshness 78 패턴 재사용). 가드 상태 추세(시계열). (P2 / M)
- **UI/UX**: active-alert 행에 심각도 색/정렬, 가드별 근거 토글. (P3 / S)

## 6. Mission Control (`/mission-control`)

현황: DB read model(36/44), compact live layout(39/57), state hardening(53),
evidence digest(57), live-error(80), 1억 KRW challenge.

- **리팩토링/하드닝**: capital map DB 정합(44) 유지, exposure 패널 empty-state는
  live-empty와 통일. (P2 / S)
- **기능**: 마일스톤 사용자 편집/단계 커스터마이즈, 다중 계정. (P3 / M)
- **UI/UX**: progress dial·milestone timeline 시각 강화, challenge 카피 밀도. (P3 / S)

## 7. News Intelligence (`/news-intel`)

현황: RSS/Atom adapter(32/33), metadata-only sentiment/risk(40), source coverage
계약(54), manual article 제거(55), live-error(80), 원문 body 미저장.

- **리팩토링/하드닝**: read-time `UNKNOWN` fallback 라벨(40) 유지. 중복 기사 dedup
  현재 단순 — URL/title 기반 클러스터링 강화. (P2 / M)
- **기능**: 소스별 신뢰도 가중, sentiment 시계열, holdings-relevance 정밀화
  (현재 feed/query 매칭 ≠ 실제 보유). (P2 / M)
- **UI/UX**: impact map 빈 상태 가독성, 소스 커버리지 칩, ticker 로고 정합. (P3 / S)

## 8. Catalyst Watch / Event Radar (`/catalyst-watch`)

현황: DB read model 승격(61), read-only 경계(64/67, manual/seed POST 제거),
source/date confidence band(58), System Ops 이벤트 ingestion 경계(70).

- **리팩토링/하드닝**: linked-news 안전 필터(외부 헤드라인) 유지. 이벤트 status
  색 계약(CONFIRMED/WINDOW/TENTATIVE/SPECULATIVE) 회귀 테스트 보강. (P2 / S)
- **기능**: **라이브 이벤트 캘린더 provider** — 현재 System Ops seed 카탈로그가
  유일 소스. 외부 캘린더 어댑터(offline-safe mock+fixture 우선)로 승격하면
  Risk Firewall event-risk 가드(항목 5)와도 연결. earnings/FOMC 리마인더. (P2 / L)
- **UI/UX**: date-confidence band·high-risk/holdings-linked 테이블 정렬, 이벤트
  expander 안의 linked-news 밀도. (P3 / S)

## 9. Trade Memory (`/trade-memory`)

현황: DB read model(49), live state band(50), 저장 후 자동 새로고침(51), form
ergonomics(52), live-error(80), 복사용 weekly markdown.

- **리팩토링/하드닝**: write-seam forbidden-wording 스캔(Slice 12) 유지. 엔트리
  업데이트 경로 정합. (P2 / S)
- **기능**: 엔트리 **편집/삭제** UI, reflection 추세(시계열), CSV/markdown export,
  mistake-tag 사용자 정의. (P2 / M)
- **UI/UX**: 폼 그룹/required 상태(52)·weekly metrics 시각화, performance bucket 정렬. (P3 / S)

## 10. System Ops (`/system-ops`) + Worker Status

현황: protocol 카드, DB audit table(38), protocol result API/detailEvidence(76),
history evidence chips(79), data-source state clarity(45/46/47), Worker Status
탭/드로어(42/43), worker cadence 감독(48).

- **리팩토링/하드닝**: `except → fixture`(system_ops GET)는 Slice 80 범위 밖이라
  아직 fixture로 떨어짐 — DB-reachable error를 live-error 패턴으로 통일. (P2 / S)
- **기능**: **history 샘플 run fixture + 비주얼 baseline 재생성**(Next Useful #1) —
  fixture 모드에서도 history 칩이 보이게. protocol run 필터/그룹, run `detailEvidence`
  히스토리 밀도. Worker: UI에서 수동 트리거, cadence stale 알림. (P2 / M)
- **UI/UX**: history-run 칩 밀도, data-source 칩·health/freshness 패널 정렬,
  command 드로어 키보드 접근. (P3 / S)

---

## 추천 시퀀싱 (가치순)

1. **P1 정합성/신뢰성**: `get_session_scope` 에러 구분(0) → frontend silent-fallback
   실패 칩(0/2/3) → `EVENT_PLACEHOLDER_GUARD` 실연결(5) → Docker env-state 테스트 audit(0).
2. **P2 공통 리팩토링**: `api/timeutil.py` 추출(0) → live-empty/error 빌더 공통화(0)
   → 오프라인 최소 콘텐츠 상태(0/82 후속).
3. **P2 탭 기능**: Catalyst 라이브 캘린더 provider(8, event-risk 가드와 묶음) →
   Market Kernel event overlay·다중 timeframe(2) → Trade Memory 편집/삭제·export(9)
   → System Ops history 샘플+baseline(10).
4. **P3 UI/UX polish**: 차트 툴팁/접근성, 상태 밴드 밀도, dead code 제거 등 묶음 처리.

각 항목은 기존 슬라이스 규약(독립 커밋 · Docker 검증 · descriptive-only · `.devmd/<NN>`
완료 노트)으로 진행한다.
