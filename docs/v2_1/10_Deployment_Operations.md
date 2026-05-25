# 10. FinSkillOS v2.1 Deployment / Operations 문서

> 문서 상태: v2.1 독립 실행형 운영 문서  
> 대상 경로: `docs/v2_1/10_Deployment_Operations.md`  
> 핵심 원칙: **FinSkillOS v2.1은 개인 투자 운영체제이므로, 로컬 안정성, 데이터 백업, 장애 복구, 보안, 운영 루틴이 개발만큼 중요하다.**

> **Current status (2026-05-25).** This document is historical design
> context from the Streamlit-first phase. The current operations workplan
> is `.devmd/14_Deployment_Operations.md`, which targets Docker Postgres
> + FastAPI `api` + Vite React `frontend` + optional Streamlit
> debug/admin + Playwright visual gates. Do not use the Streamlit MVP
> commands below as the primary product deployment path.

---

## 1. 목적

본 문서는 FinSkillOS v2.1의 개발/운영 환경, 배포 방식, 백업/복구, 데이터 관리, 로그/모니터링, 장애 대응 기준을 정의한다.

FinSkillOS는 단순 데모가 아니라 실제 개인 투자 운영에 사용하는 시스템을 목표로 한다.  
따라서 다음 조건을 만족해야 한다.

```text
1. 로컬에서 쉽게 실행 가능해야 한다.
2. PostgreSQL 데이터를 안전하게 보관해야 한다.
3. 외부 API 장애에도 앱이 완전히 죽지 않아야 한다.
4. 매일/매주 운영 루틴이 명확해야 한다.
5. 설정과 API key가 코드에 노출되지 않아야 한다.
6. 백업/복구가 쉬워야 한다.
7. 개발자/agent가 같은 환경을 재현할 수 있어야 한다.
```

---

## 2. 배포 전략 개요

FinSkillOS v2.1의 배포 전략은 단계적으로 확장한다.

| 단계 | 실행 형태 | 목적 |
|---|---|---|
| Local Dev | 로컬 Python + Docker PostgreSQL | 빠른 개발 |
| Local Full Stack | Docker Compose app + PostgreSQL | 재현 가능한 운영 |
| Personal Server | 개인 서버 / 미니 PC / DGX Spark 등 | 상시 가동 |
| Remote VPS | 클라우드 VM | 외부 접근/원격 운영 |
| Production-like | FastAPI + React 확장 가능 | 후속 버전 |

MVP 기준 추천은 다음이다.

```text
로컬 Streamlit
+ Docker PostgreSQL
+ 로컬 data volume
+ 수동/버튼 기반 refresh
```

---

## 3. 기본 시스템 구성

### 3.1 구성 요소

```text
FinSkillOS v2.1
├── Streamlit UI
├── Python Service Layer
├── PostgreSQL
├── Parquet Cache
├── JSONL Logs
└── External Data Providers
```

---

### 3.2 기본 포트

| 서비스 | 포트 | 비고 |
|---|---:|---|
| Streamlit App | 8501 | 기본 UI |
| PostgreSQL | 5432 | 로컬 DB |
| Optional FastAPI | 8000 | 후속 확장 |
| Optional Admin UI | 3000/5173 | React 전환 시 |

---

## 4. Repository 구조

권장 구조:

```text
FinSkillOS-Finance-Dashboard/
  app.py
  pyproject.toml
  requirements.txt
  docker-compose.yml
  .env.example

  finskillos/
    config.py
    db/
    services/
    signals/
    regime/
    guards/
    ui/
    optimization/
    observability/

  docs/
    v2_1/
      01_Product_Plan.md
      02_System_Design.md
      03_DB_Data_Model.md
      04_Development_Roadmap.md
      05_UI_UX_Design.md
      06_Regime_RiskGuard_Rulebook.md
      08_API_Data_Source_Design.md
      09_Test_Acceptance_Criteria.md
      10_Deployment_Operations.md

  .devmd/
    README.md
    ...

  data/
    parquet/
    exports/
    logs/

  tests/
```

---

## 5. 환경변수

### 5.1 `.env.example`

```bash
# App
APP_ENV=local
APP_NAME=FinSkillOS
APP_TIMEZONE=Asia/Seoul
LOG_LEVEL=INFO

# Database
POSTGRES_DB=finskillos
POSTGRES_USER=finskillos
POSTGRES_PASSWORD=finskillos_dev_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://finskillos:finskillos_dev_password@localhost:5432/finskillos

# Data Providers
MARKET_DATA_PROVIDER=yfinance
NEWS_PROVIDER=none
MACRO_PROVIDER=manual

# Optional API Keys
POLYGON_API_KEY=
FINNHUB_API_KEY=
ALPHA_VANTAGE_API_KEY=
NEWS_API_KEY=
FRED_API_KEY=

# Cache
CACHE_DIR=./data/cache
PARQUET_DIR=./data/parquet
LOG_DIR=./data/logs

# Risk Rules
TARGET_VALUE_KRW=100000000
MAX_SINGLE_POSITION_VALUE_KRW=10000000
MAX_SECTOR_EXPOSURE_PCT=60
MIN_CASH_RATIO_PCT=10
YELLOW_DRAWDOWN_PCT=8
RISK_REDUCTION_DRAWDOWN_PCT=10
DEFENSIVE_DRAWDOWN_PCT=15
```

---

### 5.2 보안 원칙

```text
- .env는 git에 커밋하지 않는다.
- .env.example만 커밋한다.
- API key는 로그에 출력하지 않는다.
- DB password는 운영 환경에서 별도 변경한다.
- 개인 계좌 데이터는 public repo에 업로드하지 않는다.
```

---

## 6. Docker Compose

### 6.1 개발용 PostgreSQL

```yaml
services:
  postgres:
    image: postgres:16
    container_name: finskillos-postgres
    environment:
      POSTGRES_DB: finskillos
      POSTGRES_USER: finskillos
      POSTGRES_PASSWORD: finskillos_dev_password
    ports:
      - "5432:5432"
    volumes:
      - ./docker/postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U finskillos -d finskillos"]
      interval: 10s
      timeout: 5s
      retries: 5
```

실행:

```bash
docker compose up -d postgres
```

---

### 6.2 전체 앱 컨테이너

후속 단계에서 app service를 추가한다.

```yaml
services:
  app:
    build: .
    container_name: finskillos-app
    environment:
      DATABASE_URL: postgresql+psycopg://finskillos:finskillos_dev_password@postgres:5432/finskillos
      APP_ENV: local
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
    command: streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

---

## 7. 로컬 개발 실행 절차

### 7.1 Python venv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows/WSL에서는 프로젝트를 가능하면 Linux filesystem 내부에 두는 것이 좋다.  
외장 드라이브나 `/mnt/c`, `/mnt/f` 경로에서는 symlink/권한 문제가 발생할 수 있다.

---

### 7.2 PostgreSQL 실행

```bash
docker compose up -d postgres
```

---

### 7.3 Migration

```bash
alembic upgrade head
```

---

### 7.4 앱 실행

```bash
streamlit run app.py
```

---

## 8. 운영 모드

FinSkillOS는 다음 세 가지 운영 모드를 가진다.

### 8.1 Manual Mode

```text
- 사용자가 포트폴리오 CSV를 직접 업로드
- 버튼으로 시장 데이터 refresh
- 뉴스/이벤트도 수동 입력 가능
```

MVP 기본 모드.

---

### 8.2 Assisted Mode

```text
- 시장 데이터는 일정 주기로 자동 갱신
- 뉴스/이벤트는 provider 기반으로 가져오되 사용자가 확인
- 포트폴리오는 수동 유지
```

개인 운영 권장 모드.

---

### 8.3 Always-on Mode

```text
- 개인 서버/미니 PC/DGX Spark 등에서 상시 실행
- 장전/장중/장마감 스케줄 갱신
- 알림/주간 리포트 자동 생성
```

후속 확장 모드.

---

## 9. Scheduler 운영

MVP에서는 수동 refresh를 기본으로 한다.  
Always-on 모드에서는 다음 스케줄을 사용할 수 있다.

```text
06:30 KST - US market close snapshot
09:00 KST - portfolio review summary
22:00 KST - US pre-market / macro check
23:30 KST - US market open check
Sunday 20:00 KST - weekly reflection report
```

주의:

```text
- 자동 매매는 구현하지 않는다.
- 알림은 상태 요약과 리스크 경고만 제공한다.
- 매수/매도 지시는 생성하지 않는다.
```

---

## 10. 데이터 백업

### 10.1 PostgreSQL 백업

```bash
mkdir -p backups
docker exec finskillos-postgres pg_dump -U finskillos -d finskillos > backups/finskillos_$(date +%Y%m%d_%H%M%S).sql
```

---

### 10.2 복구

```bash
cat backups/finskillos_YYYYMMDD_HHMMSS.sql | docker exec -i finskillos-postgres psql -U finskillos -d finskillos
```

---

### 10.3 Parquet / Logs 백업

```bash
tar -czf backups/finskillos_data_$(date +%Y%m%d_%H%M%S).tar.gz data/
```

---

### 10.4 백업 주기

| 데이터 | 권장 주기 |
|---|---:|
| PostgreSQL | 매일 또는 중요 작업 전 |
| data/parquet | 주 1회 |
| data/logs | 주 1회 |
| docs/.devmd | git 관리 |
| .env | 별도 안전 보관 |

---

## 11. 로그 및 모니터링

### 11.1 로그 파일

```text
data/logs/
  app.log
  data_refresh.jsonl
  alerts.jsonl
  scheduler.jsonl
  interpretation.jsonl
  errors.log
```

---

### 11.2 필수 로그 항목

```json
{
  "ts": "2026-05-15T23:30:00+09:00",
  "operation": "refresh_market_bars",
  "provider": "yfinance",
  "status": "success",
  "duration_ms": 1420,
  "tickers": 20,
  "rows_inserted": 120,
  "cache_hit": false
}
```

---

### 11.3 Healthcheck

앱에는 내부 healthcheck 함수가 있어야 한다.

```text
- DB 연결 가능 여부
- 마지막 market data refresh 시간
- 마지막 news refresh 시간
- cache directory 접근 가능 여부
- migration version
- provider status
```

UI에는 다음 상태로 표시한다.

```text
Data Health: OK / Stale / Partial / Failed
```

---

## 12. 장애 대응

### 12.1 DB 연결 실패

증상:

```text
Command Center가 열리지 않음
DB connection error
```

대응:

```bash
docker compose ps
docker compose logs postgres
docker compose restart postgres
```

확인:

```bash
docker exec -it finskillos-postgres psql -U finskillos -d finskillos
```

---

### 12.2 Migration 실패

대응 순서:

```text
1. 에러 메시지 확인
2. 현재 alembic version 확인
3. DB 백업
4. migration script 수정
5. 재실행
```

명령:

```bash
alembic current
alembic history
alembic upgrade head
```

---

### 12.3 Market Data 실패

앱은 다음을 수행해야 한다.

```text
1. 이전 캐시 표시
2. Data Health = Stale 또는 Partial
3. Command Center는 계속 렌더링
4. provider error는 logs에 기록
```

사용자에게는 다음처럼 표시한다.

```text
일부 시장 데이터가 최신 상태가 아닙니다.
마지막 성공 갱신: 2026-05-15 06:30 KST
```

---

### 12.4 News Data 실패

뉴스가 실패해도 핵심 투자 운영 화면은 살아야 한다.

```text
News & Intelligence: temporarily unavailable
Event Radar: cached/manual events shown
Command Center: no crash
```

---

### 12.5 깨진 포트폴리오 입력

예:

```text
수량 음수
market_value 없음
ticker 없음
날짜 형식 오류
```

대응:

```text
- 해당 row reject
- 에러 메시지 표시
- 전체 import 중단 여부는 옵션화
- rejected rows export 지원
```

---

## 13. 운영 루틴

### 13.1 매일 장전 / 장마감 루틴

```text
1. Portfolio snapshot 갱신
2. Market data refresh
3. Indicator 계산
4. Regime Engine 실행
5. Risk Guard 실행
6. Command Center 확인
7. Event Radar 확인
8. 오늘의 decision mode 기록
```

---

### 13.2 주간 루틴

```text
1. 주간 포트폴리오 변화 확인
2. Regime별 매매 성과 확인
3. Mistake Tags 점검
4. 다음 주 이벤트 확인
5. 목표 진행률 업데이트
6. Risk Guard threshold 조정 필요 여부 점검
```

---

### 13.3 목표 근접 루틴

평가금액이 8,500만원 이상이면 다음을 강화한다.

```text
- Completion Guard 표시
- 신규 고위험 진입 경고 강화
- drawdown guard 민감도 상향
- 현금 비중 경고 강화
- 1억 도달 시 조기 종료 플랜 표시
```

---

## 14. 배포 환경별 권장 사항

### 14.1 Local Desktop

장점:

```text
- 설정 간단
- 개인 데이터 외부 노출 최소화
- 개발/수정 빠름
```

주의:

```text
- 백업을 사용자가 직접 관리해야 함
- 장시간 자동 실행은 불안정할 수 있음
```

---

### 14.2 Personal Server / Mini PC

장점:

```text
- 상시 가동 가능
- agent/scheduler 운영 가능
- 로컬 데이터 소유권 유지
```

주의:

```text
- 전원/디스크/백업 관리 필요
- 외부 접속 시 보안 설정 필요
```

---

### 14.3 Remote VPS

장점:

```text
- 외부 접근 쉬움
- 자동화 운영 쉬움
```

주의:

```text
- 개인 투자 데이터가 클라우드에 저장됨
- 보안/인증 필수
- API key 보호 필요
```

---

## 15. 인증 / 접근 제어

MVP 로컬 앱은 인증 없이 실행할 수 있다.  
그러나 원격 접속이 가능해지는 순간 인증이 필요하다.

권장:

```text
- Basic auth 또는 reverse proxy auth
- VPN 또는 Tailscale 계열 사설망
- Public internet 직접 노출 금지
- HTTPS 적용
```

Streamlit 자체만 public으로 열어두지 않는다.

---

## 16. 데이터 보존 정책

| 데이터 | 보존 |
|---|---|
| portfolio_snapshots | 영구 |
| trades | 영구 |
| market_bars | 최소 3년 이상 |
| news_articles | 6~12개월 |
| raw provider payload | 짧게 또는 저장 안 함 |
| alerts | 영구 또는 2년 |
| logs | 3~6개월 |
| weekly reports | 영구 |

---

## 17. 업그레이드 / 롤백

### 17.1 업그레이드 전

```bash
git status
docker compose ps
mkdir -p backups
pg_dump ...
tar -czf data backup ...
```

---

### 17.2 업그레이드 순서

```text
1. 코드 pull
2. 의존성 설치
3. DB 백업
4. alembic upgrade head
5. 테스트 실행
6. 앱 실행
7. Command Center smoke 확인
```

---

### 17.3 롤백

```text
1. 앱 중지
2. 이전 git commit checkout
3. DB restore 또는 downgrade
4. 앱 재시작
5. 데이터 health 확인
```

DB migration은 rollback이 어려울 수 있으므로, 운영 DB에서는 항상 백업 후 migration 한다.

---

## 18. 성능 운영 기준

| 항목 | 목표 |
|---|---:|
| Command Center initial render | < 1.5s |
| DB healthcheck | < 200ms |
| Portfolio risk refresh | < 500ms |
| Regime calculation | < 300ms |
| 20 ticker daily refresh | < 15s |
| News refresh | provider별 가변 |
| UI tab switch | < 500ms |

성능이 느려지면 다음 순서로 확인한다.

```text
1. 외부 API 지연
2. DB index 누락
3. indicator 전체 재계산 여부
4. 차트 과다 렌더링
5. Streamlit cache 미사용
6. DataFrame 전체 표시
```

---

## 19. 운영 금지사항

```text
- public repo에 .env 또는 계좌 CSV 업로드 금지
- 외부 API 실패 시 앱 전체 중단 금지
- Streamlit 앱을 인증 없이 public internet에 노출 금지
- 자동 매수/매도 기능 구현 금지
- 뉴스 원문 전체를 무단 저장/재배포 금지
- DB migration 전 백업 생략 금지
- Command Center에서 직접 매수/매도 지시 문구 사용 금지
```

---

## 20. MVP 운영 체크리스트

```text
[ ] docker compose up -d postgres 성공
[ ] alembic upgrade head 성공
[ ] sample portfolio import 성공
[ ] Command Center 렌더링 성공
[ ] Market Regime fixture 기반 계산 성공
[ ] Risk Guard alert 생성 성공
[ ] Research Hub 샘플 차트 렌더링 성공
[ ] News & Intelligence 샘플 뉴스 렌더링 성공
[ ] DB 백업 명령 성공
[ ] 테스트 전체 통과
[ ] .env가 git에 포함되지 않음
```

---

## 21. 요약

FinSkillOS v2.1의 운영 원칙은 다음이다.

```text
Local-first
PostgreSQL-first
Backup-first
Snapshot-first
Cache-heavy
Provider-failure tolerant
No direct trading instruction
Secure by default
```

FinSkillOS는 개인 투자 판단을 돕는 운영체제이므로, 좋은 기능보다 먼저 **데이터를 잃지 않고, 앱이 죽지 않고, 사용자가 위험 상태를 이해할 수 있는 운영 안정성**을 확보해야 한다.
