# FinSkillOS v2.1

FinSkillOS v2.1 is a personal trading operating system.

## 1. 구현 순서 / 참고 문서

1. Read `.devmd/README.md`
2. Read `docs/v2_1/CONTEXT_INDEX.md`
3. Follow `.devmd` slices in numerical order when they exist
4. Use `docs/v2_1` as source-of-truth references
5. Use `prototypes/ui/os_style_mockup/index.html` as the UI direction when available
6. Do not implement direct buy/sell recommendation features

## 2. 프로젝트 레이아웃

- `finskillos/` — v2.1 application code (`ui/`, `services/`, `db/`, `regime/`, `signals/`, `guards/`)
- `docs/v2_1/` — source design documents
- `.devmd/` — agent execution instructions (slice prompts, cleanup notes, completion blocks)
- `prototypes/ui/` — HTML mockups and design references
- `data/sample/`, `data/cache/`, `data/logs/`, `data/parquet/`, `data/exports/` — local runtime data
- `tests/` — acceptance and regression tests (full suite green at 02–13)
- `legacy_v1/` — preserved v1 competition project

## 3. 빠른 시작 (Docker Compose)

처음 실행하거나 모델 스키마를 따라잡지 못한 컨테이너를 정리할 때 사용합니다.

```bash
# 0) 깨끗한 상태에서 시작 (기존 데이터 폐기)
docker compose down -v

# 1) Postgres만 먼저 띄우기
docker compose up -d postgres

# 2) 스키마를 최신(0007_trade_journal_fields)으로 마이그레이션
docker compose run --rm app alembic upgrade head

# 3) 샘플 계좌 + 57M KRW 스냅샷 시드 (선택)
docker compose run --rm app python scripts/seed_sample_data.py

# 4) Streamlit 앱 빌드 + 실행 (http://localhost:8501)
docker compose --profile app up --build
```

> **Tip.** `--profile app` 플래그가 있어야 `app` 서비스가 기동됩니다. 그렇지 않으면 Postgres만 떠 있습니다.

## 4. 이미 떠 있는 환경에서 마이그레이션만 다시 적용 (스키마 mismatch 복구)

배포가 살아 있고 데이터는 유지하고 싶을 때 — 예: `column trades.thesis does not exist` 같이
새 Slice 코드가 아직 적용 안 된 컬럼을 참조해 ProgrammingError가 날 때 — 다음을 실행합니다.

```bash
# Postgres 볼륨은 유지, 누락된 alembic 리비전만 따라잡기
docker compose run --rm app alembic upgrade head

# 떠 있는 Streamlit 컨테이너 재시작 (ORM 캐시 / 세션 초기화)
docker compose restart app
```

마이그레이션 체인 현재 상태는 다음과 같습니다 (마지막 = `head`):

```
0001_initial_foundation
0002_market_data_foundation
0003_market_regimes
0004_market_regime_factors
0005_news_intelligence
0006_event_radar
0007_trade_journal_fields   ← Slice 12에서 추가됨 (thesis, mistake_tags, sector/theme/event_key, updated_at 등)
```

`alembic upgrade head`는 idempotent — 이미 최신이면 아무 변경 없이 종료합니다.

## 5. 로컬 (Docker 없이) 실행

호스트에 Python 3.11+와 PostgreSQL이 직접 있을 때 사용합니다.

```bash
# 1) 의존성 설치
pip install -r requirements.txt

# 2) Postgres 접속 URL을 설정
export DATABASE_URL=postgresql+psycopg://finskillos:finskillos_dev_password@localhost:5432/finskillos

# 3) 스키마 최신화
python3 -m alembic upgrade head

# 4) 샘플 계좌 + 스냅샷 시드 (선택)
python3 scripts/seed_sample_data.py

# 5) Streamlit 앱 실행 (http://localhost:8501)
streamlit run app.py
```

> WSL / Windows에서 호스트 Postgres가 컨테이너 password와 다르게 초기화돼 있다면
> `docker compose down -v`로 볼륨을 초기화한 뒤 4번 과정으로 돌아오세요.

## 6. 보조 스크립트 (선택)

데이터 적재 / 점검 — 모두 `DATABASE_URL`을 읽고 idempotent하게 동작합니다.

호스트에서 (로컬 Python):

```bash
# 샘플 계좌 + 초기 스냅샷 (Slice 02)
python3 scripts/seed_sample_data.py

# Slice 04 — Mock 어댑터로 market_bars 적재
python3 scripts/refresh_market_data.py

# Slice 04 — 저장된 bar 로 indicator_snapshots 계산
python3 scripts/calculate_indicators.py

# Slice 05 — 최신 indicator로 Market Regime 한 번 분류
python3 scripts/run_regime_scan.py
```

Docker 컨테이너 안에서 (이미지가 PYTHONPATH=/app으로 빌드된 후):

```bash
docker compose run --rm app python scripts/seed_sample_data.py
docker compose run --rm app python scripts/refresh_market_data.py
docker compose run --rm app python scripts/calculate_indicators.py
docker compose run --rm app python scripts/run_regime_scan.py
```

> **`ModuleNotFoundError: No module named 'finskillos'` 가 컨테이너 안에서
> 발생하면** 이미지에 아직 `PYTHONPATH=/app`이 박혀 있지 않은 것입니다.
> 다음 중 하나로 해결합니다.
>
> 1. (권장) 이미지 다시 빌드:
>    ```bash
>    docker compose build app
>    docker compose run --rm app python scripts/seed_sample_data.py
>    ```
> 2. (임시) 한 번만 PYTHONPATH 주입해서 실행:
>    ```bash
>    docker compose run --rm -e PYTHONPATH=/app app \
>      python scripts/seed_sample_data.py
>    ```
>
> 원인 — `python scripts/foo.py` 형태로 직접 실행하면 Python은 스크립트
> 자체 디렉터리 (`/app/scripts`) 만 `sys.path` 에 prepend 하고 작업
> 디렉터리(`/app`)는 넣지 않습니다. Streamlit / alembic 은 자체 진입점이
> 별도로 `/app` 을 잡기 때문에 영향이 없습니다.

## 7. 테스트 / 품질 게이트

전체 스위트와 acceptance 게이트는 Slice 13에서 정리된 명령어로 묶여 있습니다.

```bash
# 컴파일 smoke
python3 -m compileall app.py finskillos scripts

# 전체 테스트 스위트 (현재 468 cases)
python3 -m pytest tests -q

# Slice 13 acceptance + 안전 어휘 + 성능 smoke만
python3 -m pytest \
  tests/test_acceptance_fin_skill_os.py \
  tests/test_acceptance_safety_language.py \
  tests/test_performance_budget_smoke.py \
  -q

# Alembic 마이그레이션 smoke (in-memory SQLite)
python3 -m pytest tests/integration/test_db_migrations.py -q

# Lint
python3 -m ruff check finskillos tests
```

`performance` 마커 (`tests/test_performance_budget_smoke.py`)는 CI에서 빼고 싶을 때:

```bash
python3 -m pytest tests -q -m "not performance"
```

## 8. 안전 / 해석-우선 원칙

FinSkillOS는 직접 매수 / 매도 / 실행 명령을 출력하지 않습니다. 모든 출력은
*market state / risk interpretation / portfolio constraints / watchpoints /
reflection support* 범주 안에서 작성되며, `finskillos.guards.base.assert_no_forbidden_wording`
이 view-model / journal 시점에 직접-지시 어휘를 차단합니다.
