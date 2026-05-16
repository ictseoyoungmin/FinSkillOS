# FinSkillOS v2.1 제품 기획서

> 개인 투자 운영체제형 FinSkillOS v2.1 제품 방향 및 기능 정의

| **문서 유형** | Product Plan                                                |
|---------------|-------------------------------------------------------------|
| **버전**      | v2.1                                                        |
| **작성 목적** | 개인 투자 운영체제형 FinSkillOS v2.1 개발 기준 문서         |
| **핵심 변경** | Research Hub, Index/Symbol/News 분석 영역, 해석 접근성 강화 |
| **작성일**    | 2026-05-15                                                  |

**핵심 문장: 차트는 근거이고, 상태 해석이 본문이며, 행동 모드가 결론이다.**

> **문서 사용 원칙**
>
> 본 문서는 FinSkillOS v2.1 기준의 독립 실행형 문서입니다. 이전 v2.0 문서를 참조하지 않아도 제품 목적, 구조, 개발 범위를 이해할 수 있도록 작성되었습니다. v2.1은 v2.0을 대체하며 Research Hub, Index Lab, Symbol Lab, News & Intelligence, Sector Rotation 확장을 포함합니다.

# 1. 문서 개요

본 문서는 FinSkillOS를 대회용 CSV 분석 대시보드에서 개인 투자 운영체제(Personal Trading OS)로 전환하기 위한 제품 기획서이다. v2.1에서는 기존 v2 설계에 Research Hub를 추가하여 지수 그래프, 개별 종목 차트, 뉴스/이벤트 인텔리전스를 공식 기능 영역으로 편입한다.

> **v2.1의 핵심 전환**
>
> FinSkillOS는 예측기가 아니라 의사결정 보조 OS이다. 사용자가 그래프를 직접 복합 해석하지 않아도 시장 상태, 계좌 리스크, 이벤트 영향, 행동 모드를 이해할 수 있게 만드는 것이 제품의 중심 가치이다.

# 2. 배경과 사용자 상황

- 현재 투자 목표는 5,700만원 수준의 운용자산을 1억원까지 성장시키는 것이다.

- 목표 달성 시 해당 월과 무관하게 조기 종료하고 리스크 축소 모드로 전환한다.

- 투자 방식은 스윙 3천만원, 단기 회전 2천만원 내외이며 종목당 1천만원 이상 투입하지 않는 제한을 둔다.

- 관심 섹터는 반도체, 우주, 데이터센터, 인프라, TSLA/Musk ecosystem 등이며 모두 AI CAPEX 및 Risk-On 흐름과 연결된다.

- 사용자는 여러 지표와 그래프를 동시에 해석하는 데 부담을 느낄 수 있으므로 해석 접근성을 제품 기능으로 제공해야 한다.

# 3. 문제 정의

| **문제**       | **설명**                                                                                    |
|----------------|---------------------------------------------------------------------------------------------|
| 정보 과부하    | RSI, VIX, Fear & Greed, 뉴스, 이벤트, 섹터 차트가 따로 존재하여 종합 판단이 어렵다.         |
| 해석 단절      | 차트와 숫자는 많지만 “그래서 지금 공격/방어/유지 중 무엇을 해야 하는가”로 연결되지 않는다.  |
| 계좌 맥락 부재 | 일반 차트 도구는 사용자의 보유 비중, 손절 기준, 목표 진행률, 이벤트 노출을 반영하지 않는다. |
| 목표 관리 부재 | 1억원이라는 명확한 종료 목표가 있으나 목표 근접 시 리스크를 줄이는 시스템이 없다.           |
| 복기 부재      | 어떤 시장 상태에서 돈을 벌고 잃었는지 장기적으로 학습하기 어렵다.                           |

# 4. 제품 비전

FinSkillOS v2.1의 제품 비전은 “사용자가 직접 모든 그래프를 해석하지 않아도 시장 상태와 계좌 상태를 이해하고, 목표 달성까지 큰 실수를 피하도록 돕는 개인 투자 운영체제”이다.

> **뉴스 → 해석 → 차트 확인 → 포지션 판단 → 리스크 제어 → 복기**
>
> State → Interpretation → Risk → Action → Reflection → Results

# 5. 제품 원칙

1.  차트는 근거이고, 상태 해석이 본문이며, 행동 모드가 결론이다.

2.  Command Center는 조종석이고, Research Hub는 분석실이다.

3.  모든 차트 화면에는 What happened / What does it mean / What should I watch next를 제공한다.

4.  매수/매도 추천이 아니라 리스크 인식과 행동 모드 판단을 제공한다.

5.  목표 1억원 달성 후에는 공격 지속이 아니라 조기 종료와 보호 모드를 우선한다.

6.  투자자문/확정수익/무조건적 지시 표현을 배제한다.

# 6. v2.1 정보구조

| **영역** | **탭**          | **역할**                                                              |
|----------|-----------------|-----------------------------------------------------------------------|
| Operate  | Command Center  | 오늘의 종합 상태와 행동 모드 확인                                     |
| Operate  | Market Regime   | 시장 상태, Fear & Greed, VIX, RSI, 섹터 모멘텀 해석                   |
| Operate  | Portfolio Risk  | 보유 종목, 섹터 노출, 현금 비중, drawdown, 위험 경고                  |
| Operate  | Event Radar     | SpaceX IPO, Tesla 이벤트, NVIDIA 실적, FOMC, CPI 등 촉매 관리         |
| Operate  | Goal Tracker    | 5,700만원에서 1억원까지 목표 진행률과 리스크 모드 관리                |
| Reflect  | Trade Journal   | 매매 근거, 감정 상태, 실수 태그, regime별 성과 복기                   |
| Analyze  | Research Hub    | Index Lab, Symbol Lab, News & Intelligence, Sector Rotation 심화 분석 |
| System   | Settings / Data | 목표, 티커, 섹터 매핑, 리스크 룰, 데이터 소스 관리                    |

# 7. 핵심 화면별 제품 정의

## 7.1 Command Center

- 현재 시장 상태 배너: Risk-On / Overheat Warning 등 한 줄 상태 표시.

- 목표 진행률: 57,000,000 KRW → 100,000,000 KRW, 57% 진행률.

- 오늘의 행동 모드: Selective Attack, Hold Winners, Limit New Entries, Defensive Mode 등.

- AI 해석 패널: 여러 지표의 의미를 자연어로 요약.

- 핵심 경고: 종목당 1천만원 제한, 섹터 과집중, drawdown, 현금 비중 부족 등.

- Suggested Action은 매수/매도 지시가 아니라 관리 행동 중심으로 표시.

## 7.2 Market Regime

- Fear & Greed, VIX, QQQ RSI, SMH RSI, TSLA RSI, 섹터 모멘텀 표시.

- 지표 충돌 해석 제공: RSI 과열이지만 VIX 안정이면 “추세 지속 가능+추격 제한”으로 설명.

- Regime 상태는 PANIC, RECOVERY, HEALTHY_BULL, AGGRESSIVE_RISK_ON, RISK_ON_OVERHEAT, DISTRIBUTION_RISK, DEFENSIVE_TRANSITION, RISK_OFF로 구분.

- Market Regime 화면은 차트를 전부 보여주는 곳이 아니라 상태를 이해하는 해석 화면이다.

## 7.3 Portfolio Risk

- 보유 종목 테이블: 티커, 섹터, 전략 유형, 평가금액, 비중, 수익률, thesis.

- 섹터 노출: 반도체, 우주, 데이터센터, 인프라, TSLA/Musk ecosystem, 현금.

- Risk Guard: 종목당 1천만원 제한, 섹터 집중 제한, drawdown 경보, 현금 비중 경보.

- 포지션 상세에서 Symbol Lab으로 드릴다운 가능.

## 7.4 Event Radar

- SpaceX IPO window, Tesla 이벤트, NVIDIA 실적, FOMC, CPI, 우주 발사 일정 등을 관리.

- 각 이벤트는 영향 섹터, 관련 종목, 보유 포지션 노출, 이벤트 전/후 리스크로 연결.

- Event-linked News를 통해 관련 뉴스가 발생하면 이벤트 카드와 연결.

- 이벤트는 “기회”와 “차익실현 위험”을 동시에 표시.

## 7.5 Goal Tracker

- 현재 57,000,000 KRW, 목표 100,000,000 KRW, 남은 금액 43,000,000 KRW 표시.

- 월별/연율 필요 수익률, 보수/기준/공격 시나리오, 예상 도달 시점 제공.

- Milestone Mode: Growth, Balanced, Protection, Completion 단계.

- 목표 달성 시 Challenge Complete 및 조기 종료/보호 모드 제안.

## 7.6 Trade Journal

- 매수/매도 이유, 촉매, 시장 상태, 감정 상태, 결과, 실수 태그를 기록.

- Regime별 성과, 섹터별 성과, 실수 태그별 손익을 분석.

- “나는 어떤 시장에서 돈을 벌고 어떤 상황에서 무너지는가”를 장기적으로 학습.

# 8. Research Hub 제품 정의

v2.1의 가장 큰 변경은 Research Hub의 공식 편입이다. Research Hub는 차트와 뉴스를 깊게 확인하는 분석실이며, Command Center와 Market Regime의 판단 근거를 제공한다.

| **하위 탭**         | **기능**                                      | **주요 데이터**                                  |
|---------------------|-----------------------------------------------|--------------------------------------------------|
| Index Lab           | 지수/ETF 개별 및 overlay 차트                 | SPY, QQQ, SMH, ARKX, SRVR, PAVE, VIX, DXY, TNX   |
| Symbol Lab          | 개별 종목 캔들/거래량/보조지표/내 포지션 맥락 | TSLA, NVDA, RKLB, ASTS, PLTR 등                  |
| News & Intelligence | 뉴스, 섹터, 종목, 이벤트 연결 및 AI 요약      | 보유 종목 영향도, 뉴스 톤, 포지션 관련성         |
| Sector Rotation     | 섹터별 상대강도와 자금 흐름                   | 반도체, 우주, 데이터센터, 인프라, 전력/에너지 등 |

## 8.1 Index Lab

- 개별 지수 차트와 normalized overlay 차트를 제공한다.

- 타임프레임: 1D, 5D, 1M, 3M, 6M, YTD, 1Y, 3Y.

- 보조지표: EMA 20/60/120, Bollinger Band, RSI, MACD, Volume, Drawdown.

- 해석 패널은 지수 간 상대강도와 과열/회복/위험 신호를 자연어로 설명한다.

## 8.2 Symbol Lab

- 종목별 캔들 차트, 거래량, 시간봉/일봉/주봉/월봉 전환을 제공한다.

- EMA, Bollinger Band, VWAP, RSI, MACD, 지지/저항을 표시한다.

- 내 보유 평균단가, 현재 수익률, 비중, 손절 기준, thesis, 관련 이벤트를 차트 옆에 표시한다.

- 일반 HTS가 아니라 “내 계좌 맥락이 있는 종목 분석실”이 되어야 한다.

## 8.3 News & Intelligence

- Market, Macro, Sector, Symbol, Event-linked, Position-relevant 뉴스로 분류한다.

- 뉴스는 원문 나열이 아니라 내 포지션 영향도, 긍정/부정/중립 톤, 주의점을 함께 표시한다.

- 뉴스 카드에는 제목, 출처/시간, 관련 종목, 관련 섹터, 영향도, AI 요약, 다음 체크포인트를 포함한다.

- 좋은 뉴스에도 주가 반응이 약해지는 경우를 차익실현 경고로 해석할 수 있도록 설계한다.

## 8.4 Sector Rotation

- 섹터별 1주/1개월/3개월 수익률, RSI, 거래량 증가율, 상대강도, 모멘텀 점수를 제공한다.

- 내 포트폴리오가 현재 주도 섹터에 과도하게 집중되어 있는지 분석한다.

- 섹터 로테이션 발생 시 Command Center와 Portfolio Risk에 경고를 전파한다.

# 9. 사용자 플로우

| **상황**       | **사용 흐름**                                      | **결과**                                |
|----------------|----------------------------------------------------|-----------------------------------------|
| 장 시작 전     | Command Center → Market Regime → Event Radar       | 오늘의 리스크 모드와 주의 이벤트 확인   |
| 관심 종목 분석 | Research Hub \> Symbol Lab → News & Intelligence   | 차트와 뉴스, 내 포지션 맥락을 함께 확인 |
| 과열 경고 발생 | Portfolio Risk → Risk Control → Goal Tracker       | 포지션 크기와 현금 비중 점검            |
| 주말 복기      | Trade Journal → Regime Performance → Weekly Report | 수익/손실 패턴과 실수 태그 확인         |
| 1억 근접       | Goal Tracker → Protection Mode → Command Center    | 공격성 축소와 조기 종료 준비            |

# 10. MVP 범위

- PostgreSQL-first 데이터 구조는 유지한다.

- 초기 데이터 입력은 수동/CSV 업로드를 허용하되 추후 API 연동을 고려한다.

- Command Center, Goal Tracker, Portfolio Risk, Market Regime을 1차 MVP로 구현한다.

- Research Hub는 Index Lab과 Symbol Lab의 기본 차트부터 구현하고, 뉴스는 구조를 먼저 잡은 뒤 데이터 소스를 확장한다.

- LLM 해석은 온디맨드/캐시 기반으로 두며 기본 해석은 룰/템플릿 기반으로 제공한다.

# 11. 성공 지표

| **지표**    | **측정 기준**                                                                            |
|-------------|------------------------------------------------------------------------------------------|
| 해석 접근성 | 사용자가 30초 내 현재 시장 상태와 행동 모드를 이해할 수 있는가                           |
| 리스크 제어 | 종목당 1천만원 제한, drawdown, 섹터 과집중 경고가 즉시 작동하는가                        |
| 목표 관리   | 1억원 목표 진행률과 목표 근접 리스크 모드가 일관되게 표시되는가                          |
| 복기 품질   | Regime/섹터/실수 태그별 성과를 주간 단위로 검토할 수 있는가                              |
| 성능        | Command Center 초기 렌더링 1.5초 이내, 포트폴리오 리스크 갱신 500ms 이내를 목표로 하는가 |

# 12. 비범위와 주의사항

- FinSkillOS는 투자자문 서비스가 아니며 매수/매도 지시를 직접 제공하지 않는다.

- 수익률을 보장하거나 특정 종목의 상승을 단정하지 않는다.

- 초기 MVP에서 증권사 실계좌 자동 연동은 필수 범위가 아니다.

- 뉴스 데이터는 저작권과 라이선스 조건을 준수해야 하며 원문 대량 저장보다 요약/메타데이터 중심으로 설계한다.

- 모든 해석은 판단 보조이며 최종 의사결정은 사용자에게 있다.

# 13. v2.1 변경 요약

| **구분**  | **내용**                                                                                                    |
|-----------|-------------------------------------------------------------------------------------------------------------|
| v2        | Command Center, Market Regime, Portfolio Risk, Event Radar, Goal Tracker, Trade Journal 중심                |
| v2.1      | Research Hub 추가: Index Lab, Symbol Lab, News & Intelligence, Sector Rotation                              |
| 변경 이유 | 지수/종목/뉴스 분석을 별도 분석실로 분리해 운영 화면을 단순하게 유지하면서도 심화 분석을 가능하게 하기 위해 |
| 제품 효과 | 일반 HTS가 아니라 계좌 맥락과 시장 해석이 결합된 투자 운영체제로 확장                                       |

# 14. 다음 문서 연결

- DB/Data Model 설계서는 PostgreSQL 테이블, 인덱스, materialized view, JSONB 사용 위치를 구체화한다.

- 개발 로드맵은 Phase 0~7의 구현 순서, 완료 기준, 테스트 기준을 제공한다.

- 추후 UI/UX 설계서는 Research Hub v2.1 목업, 차트 드릴다운, 뉴스 카드, 해석 패널을 화면 단위로 정의한다.

- Regime/Risk Guard 룰북은 시장 상태 판정과 리스크 경고 문구를 deterministic rule로 고정한다.
