# 126 — Runtime Settings Overlay In Ops

Date: 2026-06-02

## Source Queue Item

Follow-up request to worker/job queue work:

> Ops 탭에서 런타임 설정을 바꿔 저장하고, 서버 재시작/큐 실행 시에도 지속되도록 한다.

## Scope

- `.env` 기본값은 부팅 기본으로 유지한다.
- Ops 탭에 런타임 설정 편집 UI를 추가한다.
- 설정 변경은 DB에 영속 저장하고 재부팅 시에도 재적용한다.
- 런타임 갱신은 `.env`를 기준으로 하되 DB 오버레이를 덮어쓰기 우선순위로 사용한다.
- refresh 관련 운영 버튼은 job payload에 현재 유효 설정을 담아 worker가 동일 값으로 실행되게 한다.

## Implementation

- `finskillos/runtime_settings.py`
  - DB 오버레이(`system_ops_settings`) + `.env` + 런타임 오버라이드를 병합해 설정 해석.
  - 지원 key 목록과 `read_runtime_value/read_runtime_int/read_runtime_bool/read_runtime_csv` 추가.
  - `runtime_setting_snapshot_for_job_queue()`로 job payload 메타 생성.
- `finskillos/db/models/system_ops.py` / `finskillos/db/repositories/system_ops_repo.py`
  - `system_ops_settings` 단건 JSON 테이블·레포지토리 추가.
- `finskillos/db/migrations/versions/0015_system_ops_settings.py`
  - 신규 migration + 기본 empty json 행 생성.
- `api/routes/system_ops.py`
  - `/api/system-ops/runtime-settings` GET/PATCH 추가.
  - 시스템 전체 `/api/system-ops` 응답에 `runtimeSettings` 반영.
  - `refresh-*` protocol enqueue 시 `payload.runtime_settings` 포함.
  - worker 스토리 관련 타이밍/안전값 산출을 `read_runtime_*` 계열로 전환.
- `finskillos/services/watchlist_refresh_policy.py`, `finskillos/services/news_feed_policy.py`, `scripts/refresh_worker.py`
  - `runtime_overrides`를 통해 큐 payload 반영 실행.
- `frontend/src/pages/system-ops/SystemOpsPage.tsx`, `frontend/src/features/system-ops/*`
  - Ops 탭에 `Runtime Settings` 탭 추가.
  - 설정 편집/저장/Reset, 변경 감지/저장 피드백 반영.
  - boolean은 체크박스로, 나머지는 텍스트/숫자 입력으로 구성해 공간 낭비를 줄인 2컬럼 카드 레이아웃 적용.
- `tests/test_api_system_ops.py`, `tests/test_worker_jobs.py`
  - 런타임 설정 저장/검증/오버라이드 enqueue 반영/드레인 적용 테스트 추가.
- `tests/integration/test_db_migrations.py`
  - `system_ops_settings` 존재 검증 추가.
- `frontend/src/mocks/fixtures/systemOps.fixture.ts`, `api/fixtures/system_ops.py`, `.env.example`, `docs/WORKER_QUEUE_AND_API_SPEC.md`
  - runtime setting 기본값/스펙 반영 및 문서 갱신.

## Verification

```bash

docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api python -m ruff check api/routes/system_ops.py tests/test_api_system_ops.py tests/test_worker_jobs.py tests/test_watchlist_refresh_policy.py tests/integration/test_db_migrations.py scripts/refresh_worker.py finskillos/db/migrations/versions/0015_system_ops_settings.py
docker compose -f docker-compose.yml run --rm --no-deps api timeout 600 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py tests/test_worker_jobs.py tests/test_watchlist_refresh_policy.py tests/integration/test_db_migrations.py -q
docker compose -f docker-compose.yml run --rm --no-deps api python -m pytest tests/integration/test_db_migrations.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
```

## Result

- API lint: `PASS`
- API tests: `PASS` (`test_api_system_ops.py`, `test_worker_jobs.py`, `test_watchlist_refresh_policy.py`, `tests/integration/test_db_migrations.py`)
- Migration index smoke: `PASS`
- Web build: `PASS`

## Known issues

- Settings UI는 안전 운영 범위(샘플값/오프라인 모드)에서 즉시 적용 미리보기를 유지하지 않고 다음 API 조회 시 반영되므로, 저장 직후에는 결과 재조회/노티스로 동기화를 보장해야 한다.

## Review follow-up — polish & hardening (2026-06-02)

검토 중 발견한 항목 정리/보강:

- **Lint**: 변경 파일 전체 기준 `ruff` import-ordering 4건(I001) 정리 →
  `ruff check` 전체 통과. (원 노트의 lint PASS는 일부 파일만 검사했음.)
- **Dead code**: `runtime_settings.py::_read_overrides`의 도달 불가 `return {}` 제거.
- **Hardening (mock 어댑터)**: Runtime Settings의 Market adapter를 자유 입력 →
  `yahoo`/`mock` **select**로 변경하고, `mock` 선택 시 "synthetic bars가 라이브
  차트를 desync시킬 수 있다"는 경고를 노출(슬라이스 111 톱니 교훈). 오타로 잘못된
  어댑터를 저장하는 경로 차단.
- **Polish**: 저장 알림 tone 코딩(success/error/info) + `saveError` 병합, 숫자
  입력 `min`(기본 1), "Saving…" ellipsis, 변경 없을 때 Reset 비활성화.

검증: web `npm run build && lint` ✅(0 errors), `pytest test_api_system_ops
test_worker_jobs` ✅, 전체 로컬 스위트 ✅, system-ops structural+visual ✅
(3-tab 탭바 반영으로 baseline 재생성).
