Asset (Collapsed)​Copy link
본인 계좌의 보유 자산 현황을 조회하는 그룹입니다. 종목별 보유 수량·매입가·평가금액·손익과 함께 계좌 전체의 합산 요약을 제공합니다. 국내(KR)·미국(US) 주식이 대상이며 해외 옵션·채권 등은 제외됩니다. 손익률은 원화(KRW) 환산 기준으로 계산됩니다. 호출 시 액세스 토큰과 X-Tossinvest-Account 헤더가 함께 필요합니다.

보유 주식 조회​Copy link
보유 주식 정보를 조회합니다. 국내(KR)·미국(US) 주식만 포함하며, 해외 옵션·채권은 제외합니다. 보유 종목이 없으면 요약 금액은 0이고 items는 빈 배열입니다.

Rate Limits Group: ASSET

Query Parameters
symbolCopy link to symbol
Type:string
Pattern:^[A-Za-z0-9.\-]+$
Example
종목 심볼. KR: 6자리 숫자 (예: 005930), US: 티커 (예: AAPL). 영문 대/소문자, 숫자, '.', '-' 만 허용한다. 제공 시 해당 종목만 필터링하여 반환하며, 요약 필드도 해당 종목 기준으로 재계산합니다. 미제공 시 전체 보유 종목을 반환합니다.

Headers
X-Tossinvest-AccountCopy link to X-Tossinvest-Account
Type:integer
Format:int64
required
Example
API 요청 시 사용할 계좌의 accountSeq. GET /api/v1/accounts 응답의 accountSeq 값을 사용합니다.

Responses

200
application/json
성공

성공 응답 envelope. 200 응답에 사용됩니다. 각 엔드포인트의 성공 응답 스키마는 allOf 로 본 스키마를 상속하며 result 를 구체 타입으로 specialize 합니다. 실패 응답은 별도의 ErrorResponse 스키마를 사용합니다 (4xx/5xx). result 와 error 는 동시에 나타나지 않습니다.

resultCopy link to result
Type:object · HoldingsOverview
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
dailyProfitLoss
Type:object · OverviewDailyProfitLoss
required
일간 손익. 전체 보유 종목의 통화별 합산

Hide Child Attributesfor dailyProfitLoss
amount
Type:object · Price
required
통화별 합산 금액. 각 통화 필드는 해당 통화로 거래된 종목의 합만 포함합니다 (환율 환산을 통한 통화 간 합산 미포함).

Hide Child Attributesfor amount
krw
Type:string
max length:  
30
Format:decimal
required
KRW로 거래되는 국내 종목의 합산 금액. 국내 종목이 없으면 0

usd
Type:string
max length:  
30
Format:decimal
USD로 거래되는 해외 종목의 합산 금액. 해외 종목이 없으면 null

rate
Type:string
max length:  
30
Format:decimal
required
Example
일간 손익률 (소수비율). 전체 자산을 현재 환율로 원화 환산한 기준. 0.0185 = 1.85%

items
Type:array object[] · HoldingsItem[]
required
보유 종목 목록. 보유 종목이 없으면 빈 배열

Hide Child Attributesfor items
averagePurchasePrice
Type:string
max length:  
30
Format:decimal
required
Example
매수 평균가. 거래 통화(currency) 기준

cost
Type:object · Cost
required
비용. 거래 통화(currency) 기준

Hide Child Attributesfor cost
commission
Type:string
max length:  
30
Format:decimal
required
Example
수수료

tax
Type:string
max length:  
30
Format:decimal
Example
세금. 세금이 없는 경우 null

currency
Type:string · Currency
enum
required
통화 코드.

KRW: 한국 원화
USD: 미국 달러
클라이언트는 unknown enum 값을 허용하도록 구현해야 합니다.

values
KRW
USD
dailyProfitLoss
Type:object · DailyProfitLoss
required
일간 손익. 거래 통화(currency) 기준

Hide Child Attributesfor dailyProfitLoss
amount
Type:string
max length:  
30
Format:decimal
required
Example
일간 손익금액

rate
Type:string
max length:  
30
Format:decimal
required
Example
일간 손익률. 소수비율 (0.0141 = 1.41%)

lastPrice
Type:string
max length:  
30
Format:decimal
required
Example
현재가. 거래 통화(currency) 기준

marketCountry
Type:string · MarketCountry
enum
required
시장 국가 구분.

KR: 국내 주식 (KRX)
US: 미국 주식 (NYSE, NASDAQ 등)
클라이언트는 unknown enum 값을 허용하도록 구현해야 합니다.

values
KR
US
marketValue
Type:object · MarketValue
required
시장 평가. 거래 통화(currency) 기준

Hide Child Attributesfor marketValue
amount
Type:string
max length:  
30
Format:decimal
required
Example
시장 평가금액

amountAfterCost
Type:string
max length:  
30
Format:decimal
required
Example
세금/수수료 공제 후 평가금액

purchaseAmount
Type:string
max length:  
30
Format:decimal
required
Example
매입금액

name
Type:string
required
Example
종목명

profitLoss
Type:object · ProfitLoss
required
손익. 거래 통화(currency) 기준

Hide Child Attributesfor profitLoss
amount
Type:string
max length:  
30
Format:decimal
required
Example
손익금액

amountAfterCost
Type:string
max length:  
30
Format:decimal
required
Example
세금/수수료 공제 후 손익금액

rate
Type:string
max length:  
30
Format:decimal
required
Example
손익률. 소수비율 (0.1077 = 10.77%)

rateAfterCost
Type:string
max length:  
30
Format:decimal
required
Example
세금/수수료 공제 후 손익률. 소수비율 (0.0846 = 8.46%)

quantity
Type:string
max length:  
30
Format:decimal
required
Example
보유 수량

symbol
Type:string
required
Example
종목 심볼. KR: 6자리 숫자, US: 티커

marketValue
Type:object · OverviewMarketValue
required
시장 평가금액. 전체 보유 종목의 통화별 합산

Hide Child Attributesfor marketValue
amount
Type:object · Price
required
통화별 합산 금액. 각 통화 필드는 해당 통화로 거래된 종목의 합만 포함합니다 (환율 환산을 통한 통화 간 합산 미포함).

Hide Child Attributesfor amount
krw
Type:string
max length:  
30
Format:decimal
required
KRW로 거래되는 국내 종목의 합산 금액. 국내 종목이 없으면 0

usd
Type:string
max length:  
30
Format:decimal
USD로 거래되는 해외 종목의 합산 금액. 해외 종목이 없으면 null

amountAfterCost
Type:object · Price
required
통화별 합산 금액. 각 통화 필드는 해당 통화로 거래된 종목의 합만 포함합니다 (환율 환산을 통한 통화 간 합산 미포함).

Hide Child Attributesfor amountAfterCost
krw
Type:string
max length:  
30
Format:decimal
required
KRW로 거래되는 국내 종목의 합산 금액. 국내 종목이 없으면 0

usd
Type:string
max length:  
30
Format:decimal
USD로 거래되는 해외 종목의 합산 금액. 해외 종목이 없으면 null

profitLoss
Type:object · OverviewProfitLoss
required
손익. 전체 보유 종목의 통화별 합산

Hide Child Attributesfor profitLoss
amount
Type:object · Price
required
통화별 합산 금액. 각 통화 필드는 해당 통화로 거래된 종목의 합만 포함합니다 (환율 환산을 통한 통화 간 합산 미포함).

Hide Child Attributesfor amount
krw
Type:string
max length:  
30
Format:decimal
required
KRW로 거래되는 국내 종목의 합산 금액. 국내 종목이 없으면 0

usd
Type:string
max length:  
30
Format:decimal
USD로 거래되는 해외 종목의 합산 금액. 해외 종목이 없으면 null

amountAfterCost
Type:object · Price
required
통화별 합산 금액. 각 통화 필드는 해당 통화로 거래된 종목의 합만 포함합니다 (환율 환산을 통한 통화 간 합산 미포함).

Hide Child Attributesfor amountAfterCost
krw
Type:string
max length:  
30
Format:decimal
required
KRW로 거래되는 국내 종목의 합산 금액. 국내 종목이 없으면 0

usd
Type:string
max length:  
30
Format:decimal
USD로 거래되는 해외 종목의 합산 금액. 해외 종목이 없으면 null

rate
Type:string
max length:  
30
Format:decimal
required
Example
손익률 (소수비율). 전체 자산을 현재 환율로 원화 환산한 기준. 0.1516 = 15.16%

rateAfterCost
Type:string
max length:  
30
Format:decimal
required
Example
세금/수수료 공제 후 손익률 (소수비율). 전체 자산을 현재 환율로 원화 환산한 기준. 0.1406 = 14.06%

totalPurchaseAmount
Type:object · Price
required
통화별 합산 금액. 각 통화 필드는 해당 통화로 거래된 종목의 합만 포함합니다 (환율 환산을 통한 통화 간 합산 미포함).

Hide Child Attributesfor totalPurchaseAmount
krw
Type:string
max length:  
30
Format:decimal
required
KRW로 거래되는 국내 종목의 합산 금액. 국내 종목이 없으면 0

usd
Type:string
max length:  
30
Format:decimal
USD로 거래되는 해외 종목의 합산 금액. 해외 종목이 없으면 null


400
application/json
X-Tossinvest-Account 헤더 누락

Type:object · ErrorResponse
에러 응답 envelope. 4xx/5xx 응답에 사용됩니다. 성공 응답은 별도의 ApiResponse 스키마를 사용합니다.

error
Type:object · ApiError
required
에러 객체. 에러 식별에 필요한 최소 정보(requestId, code, message)와 필요 시 해결 힌트(data)를 포함합니다.

Hide Child Attributesfor error
code
Type:string
required
Example
에러 코드. flat string 식별자. 도메인 에러는 이유를 직접 표현하는 단일 식별자 (예: invalid-request, order-not-found) 를 사용합니다. 클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

message
Type:string
required
Example
사용자에게 노출 가능한 에러 메시지. 내부 정책상 노출이 제한되는 경우 빈 문자열로 내려갈 수 있으므로 클라이언트는 code 기반으로 메시지를 자체 매핑할 것을 권장합니다.

requestId
Type:string
required
Example
요청을 식별하는 고유 ID. 응답 헤더 X-Request-Id 와 동일한 값입니다. 토스증권 CS 문의 시 첨부를 권장합니다.

data
Type:object | null
에러 해결 힌트. 에러 코드별로 포함 여부와 키 구조가 다르며, 없는 경우 필드 자체가 생략됩니다. 모든 표준 키가 항상 함께 내려가지 않으며, 각 에러 코드에 해당하는 서브셋만 포함됩니다.

표준 키 (camelCase)
키	타입	설명
field	string	검증 실패 원인 필드. 외부 API 에 노출된 이름 (request body JSON key 또는 query parameter name) 을 사용합니다. 복수 필드는 쉼표로 구분 (예: "quantity,orderAmount").
allowedValues	string[]	enum 후보 값 전체.
allowedConditions	object	조건부 허용 규칙 (marketCountry / orderType / side 등).
constraint	object	필드 제약 (min / max / integerOnly / step).
format	string	포맷 규칙명 (예: decimal).
pattern	string	정규식.
maxLength	number	문자열 길이 상한.
limits	object	금액 / 수량 한도 (threshold / minimum / maximum + currency).
retryAfterAt	string	절대 재시도 시각 (ISO 8601 offset, KST).
retryAfterSeconds	number	상대 재시도 시각 (초).
tickSize	string	호가 단위.
nearestPrices	string[]	근접 유효 가격 ([lower, upper]).
구체적인 에러 코드별 data 예시는 각 엔드포인트의 4xx / 5xx 응답 예시를 참고합니다.

Hide Child Attributesfor data
propertyName
Type:anything

401
application/json
인증 실패. WWW-Authenticate: Bearer ... 헤더가 함께 내려갑니다.

Hide Headers
WWW-AuthenticateCopy link to WWW-Authenticate
Type:string
OAuth 2.0 Bearer 토큰 챌린지. 메시지에 non-ASCII 문자가 포함되는 경우 error_description 파라미터는 생략됩니다.

Type:object · ErrorResponse
Examples
에러 응답 envelope. 4xx/5xx 응답에 사용됩니다. 성공 응답은 별도의 ApiResponse 스키마를 사용합니다.

error
Type:object · ApiError
required
에러 객체. 에러 식별에 필요한 최소 정보(requestId, code, message)와 필요 시 해결 힌트(data)를 포함합니다.

Hide Child Attributesfor error
code
Type:string
required
Example
에러 코드. flat string 식별자. 도메인 에러는 이유를 직접 표현하는 단일 식별자 (예: invalid-request, order-not-found) 를 사용합니다. 클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

message
Type:string
required
Example
사용자에게 노출 가능한 에러 메시지. 내부 정책상 노출이 제한되는 경우 빈 문자열로 내려갈 수 있으므로 클라이언트는 code 기반으로 메시지를 자체 매핑할 것을 권장합니다.

requestId
Type:string
required
Example
요청을 식별하는 고유 ID. 응답 헤더 X-Request-Id 와 동일한 값입니다. 토스증권 CS 문의 시 첨부를 권장합니다.

data
Type:object | null
에러 해결 힌트. 에러 코드별로 포함 여부와 키 구조가 다르며, 없는 경우 필드 자체가 생략됩니다. 모든 표준 키가 항상 함께 내려가지 않으며, 각 에러 코드에 해당하는 서브셋만 포함됩니다.

표준 키 (camelCase)
키	타입	설명
field	string	검증 실패 원인 필드. 외부 API 에 노출된 이름 (request body JSON key 또는 query parameter name) 을 사용합니다. 복수 필드는 쉼표로 구분 (예: "quantity,orderAmount").
allowedValues	string[]	enum 후보 값 전체.
allowedConditions	object	조건부 허용 규칙 (marketCountry / orderType / side 등).
constraint	object	필드 제약 (min / max / integerOnly / step).
format	string	포맷 규칙명 (예: decimal).
pattern	string	정규식.
maxLength	number	문자열 길이 상한.
limits	object	금액 / 수량 한도 (threshold / minimum / maximum + currency).
retryAfterAt	string	절대 재시도 시각 (ISO 8601 offset, KST).
retryAfterSeconds	number	상대 재시도 시각 (초).
tickSize	string	호가 단위.
nearestPrices	string[]	근접 유효 가격 ([lower, upper]).
구체적인 에러 코드별 data 예시는 각 엔드포인트의 4xx / 5xx 응답 예시를 참고합니다.

Hide Child Attributesfor data
propertyName
Type:anything

404
application/json
종목을 찾을 수 없음

Type:object · ErrorResponse
에러 응답 envelope. 4xx/5xx 응답에 사용됩니다. 성공 응답은 별도의 ApiResponse 스키마를 사용합니다.

error
Type:object · ApiError
required
에러 객체. 에러 식별에 필요한 최소 정보(requestId, code, message)와 필요 시 해결 힌트(data)를 포함합니다.

Hide Child Attributesfor error
code
Type:string
required
Example
에러 코드. flat string 식별자. 도메인 에러는 이유를 직접 표현하는 단일 식별자 (예: invalid-request, order-not-found) 를 사용합니다. 클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

message
Type:string
required
Example
사용자에게 노출 가능한 에러 메시지. 내부 정책상 노출이 제한되는 경우 빈 문자열로 내려갈 수 있으므로 클라이언트는 code 기반으로 메시지를 자체 매핑할 것을 권장합니다.

requestId
Type:string
required
Example
요청을 식별하는 고유 ID. 응답 헤더 X-Request-Id 와 동일한 값입니다. 토스증권 CS 문의 시 첨부를 권장합니다.

data
Type:object | null
에러 해결 힌트. 에러 코드별로 포함 여부와 키 구조가 다르며, 없는 경우 필드 자체가 생략됩니다. 모든 표준 키가 항상 함께 내려가지 않으며, 각 에러 코드에 해당하는 서브셋만 포함됩니다.

표준 키 (camelCase)
키	타입	설명
field	string	검증 실패 원인 필드. 외부 API 에 노출된 이름 (request body JSON key 또는 query parameter name) 을 사용합니다. 복수 필드는 쉼표로 구분 (예: "quantity,orderAmount").
allowedValues	string[]	enum 후보 값 전체.
allowedConditions	object	조건부 허용 규칙 (marketCountry / orderType / side 등).
constraint	object	필드 제약 (min / max / integerOnly / step).
format	string	포맷 규칙명 (예: decimal).
pattern	string	정규식.
maxLength	number	문자열 길이 상한.
limits	object	금액 / 수량 한도 (threshold / minimum / maximum + currency).
retryAfterAt	string	절대 재시도 시각 (ISO 8601 offset, KST).
retryAfterSeconds	number	상대 재시도 시각 (초).
tickSize	string	호가 단위.
nearestPrices	string[]	근접 유효 가격 ([lower, upper]).
구체적인 에러 코드별 data 예시는 각 엔드포인트의 4xx / 5xx 응답 예시를 참고합니다.

Hide Child Attributesfor data
propertyName
Type:anything

429
application/json
요청 한도 초과. 포함 헤더의 의미는 아래 headers 정의를 참조합니다.

Hide Headers
X-RateLimit-LimitCopy link to X-RateLimit-Limit
Type:integer
현재 허용된 초당 요청 수 (burst capacity)

X-RateLimit-RemainingCopy link to X-RateLimit-Remaining
Type:integer
현재 버킷에 남은 토큰 수. 429 시 0.

X-RateLimit-ResetCopy link to X-RateLimit-Reset
Type:integer
토큰 1 개가 재충전될 때까지 예상 초

Retry-AfterCopy link to Retry-After
Type:integer
재시도 권장 초

Type:object · ErrorResponse
에러 응답 envelope. 4xx/5xx 응답에 사용됩니다. 성공 응답은 별도의 ApiResponse 스키마를 사용합니다.

error
Type:object · ApiError
required
에러 객체. 에러 식별에 필요한 최소 정보(requestId, code, message)와 필요 시 해결 힌트(data)를 포함합니다.

Hide Child Attributesfor error
code
Type:string
required
Example
에러 코드. flat string 식별자. 도메인 에러는 이유를 직접 표현하는 단일 식별자 (예: invalid-request, order-not-found) 를 사용합니다. 클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

message
Type:string
required
Example
사용자에게 노출 가능한 에러 메시지. 내부 정책상 노출이 제한되는 경우 빈 문자열로 내려갈 수 있으므로 클라이언트는 code 기반으로 메시지를 자체 매핑할 것을 권장합니다.

requestId
Type:string
required
Example
요청을 식별하는 고유 ID. 응답 헤더 X-Request-Id 와 동일한 값입니다. 토스증권 CS 문의 시 첨부를 권장합니다.

data
Type:object | null
에러 해결 힌트. 에러 코드별로 포함 여부와 키 구조가 다르며, 없는 경우 필드 자체가 생략됩니다. 모든 표준 키가 항상 함께 내려가지 않으며, 각 에러 코드에 해당하는 서브셋만 포함됩니다.

표준 키 (camelCase)
키	타입	설명
field	string	검증 실패 원인 필드. 외부 API 에 노출된 이름 (request body JSON key 또는 query parameter name) 을 사용합니다. 복수 필드는 쉼표로 구분 (예: "quantity,orderAmount").
allowedValues	string[]	enum 후보 값 전체.
allowedConditions	object	조건부 허용 규칙 (marketCountry / orderType / side 등).
constraint	object	필드 제약 (min / max / integerOnly / step).
format	string	포맷 규칙명 (예: decimal).
pattern	string	정규식.
maxLength	number	문자열 길이 상한.
limits	object	금액 / 수량 한도 (threshold / minimum / maximum + currency).
retryAfterAt	string	절대 재시도 시각 (ISO 8601 offset, KST).
retryAfterSeconds	number	상대 재시도 시각 (초).
tickSize	string	호가 단위.
nearestPrices	string[]	근접 유효 가격 ([lower, upper]).
구체적인 에러 코드별 data 예시는 각 엔드포인트의 4xx / 5xx 응답 예시를 참고합니다.

Hide Child Attributesfor data
propertyName
Type:anything

500
application/json
보유 자산 조회 중 일시적 오류

Type:object · ErrorResponse
에러 응답 envelope. 4xx/5xx 응답에 사용됩니다. 성공 응답은 별도의 ApiResponse 스키마를 사용합니다.

error
Type:object · ApiError
required
에러 객체. 에러 식별에 필요한 최소 정보(requestId, code, message)와 필요 시 해결 힌트(data)를 포함합니다.

Hide Child Attributesfor error
code
Type:string
required
Example
에러 코드. flat string 식별자. 도메인 에러는 이유를 직접 표현하는 단일 식별자 (예: invalid-request, order-not-found) 를 사용합니다. 클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

message
Type:string
required
Example
사용자에게 노출 가능한 에러 메시지. 내부 정책상 노출이 제한되는 경우 빈 문자열로 내려갈 수 있으므로 클라이언트는 code 기반으로 메시지를 자체 매핑할 것을 권장합니다.

requestId
Type:string
required
Example
요청을 식별하는 고유 ID. 응답 헤더 X-Request-Id 와 동일한 값입니다. 토스증권 CS 문의 시 첨부를 권장합니다.

data
Type:object | null
에러 해결 힌트. 에러 코드별로 포함 여부와 키 구조가 다르며, 없는 경우 필드 자체가 생략됩니다. 모든 표준 키가 항상 함께 내려가지 않으며, 각 에러 코드에 해당하는 서브셋만 포함됩니다.

표준 키 (camelCase)
키	타입	설명
field	string	검증 실패 원인 필드. 외부 API 에 노출된 이름 (request body JSON key 또는 query parameter name) 을 사용합니다. 복수 필드는 쉼표로 구분 (예: "quantity,orderAmount").
allowedValues	string[]	enum 후보 값 전체.
allowedConditions	object	조건부 허용 규칙 (marketCountry / orderType / side 등).
constraint	object	필드 제약 (min / max / integerOnly / step).
format	string	포맷 규칙명 (예: decimal).
pattern	string	정규식.
maxLength	number	문자열 길이 상한.
limits	object	금액 / 수량 한도 (threshold / minimum / maximum + currency).
retryAfterAt	string	절대 재시도 시각 (ISO 8601 offset, KST).
retryAfterSeconds	number	상대 재시도 시각 (초).
tickSize	string	호가 단위.
nearestPrices	string[]	근접 유효 가격 ([lower, upper]).
구체적인 에러 코드별 data 예시는 각 엔드포인트의 4xx / 5xx 응답 예시를 참고합니다.

Hide Child Attributesfor data
propertyName
Type:anything
Request Example forget/api/v1/holdings
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/holdings?symbol=005930' \
  --header 'X-Tossinvest-Account: 1' \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:400
Status:401
Status:404
Status:429
Status:500
{
  "result": {
    "totalPurchaseAmount": {
      "krw": "6500000",
      "usd": "1553"
    },
    "marketValue": {
      "amount": {
        "krw": "7200000",
        "usd": "1785"
      },
      "amountAfterCost": {
        "krw": "7050000",
        "usd": "1771.43"
      }
    },
    "profitLoss": {
      "amount": {
        "krw": "700000",
        "usd": "232"
      },
      "amountAfterCost": {
        "krw": "550000",
        "usd": "218.43"
      },
      "rate": "0.1179",
      "rateAfterCost": "0.0983"
    },
    "dailyProfitLoss": {
      "amount": {
        "krw": "100000",
        "usd": "25"
      },
      "rate": "0.0141"
    },
    "items": [
      {
        "symbol": "005930",
        "name": "삼성전자",
        "marketCountry": "KR",
        "currency": "KRW",
        "quantity": "100",
        "lastPrice": "72000",
        "averagePurchasePrice": "65000",
        "marketValue": {
          "purchaseAmount": "6500000",
          "amount": "7200000",
          "amountAfterCost": "7050000"
        },
        "profitLoss": {
          "amount": "700000",
          "amountAfterCost": "550000",
          "rate": "0.1077",
          "rateAfterCost": "0.0846"
        },
        "dailyProfitLoss": {
          "amount": "100000",
          "rate": "0.0141"
        },
        "cost": {
          "commission": "14400",
          "tax": "135600"
        }
      },
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "marketCountry": "US",
        "currency": "USD",
        "quantity": "10",
        "lastPrice": "178.5",
        "averagePurchasePrice": "155.3",
        "marketValue": {
          "purchaseAmount": "1553",
          "amount": "1785",
          "amountAfterCost": "1771.43"
        },
        "profitLoss": {
          "amount": "232",
          "amountAfterCost": "218.43",
          "rate": "0.1494",
          "rateAfterCost": "0.1406"
        },
        "dailyProfitLoss": {
          "amount": "25",
          "rate": "0.0142"
        },
        "cost": {
          "commission": "3.57",
          "tax": "10"
        }
      }
    ]
  }
}


보유 종목 있음 (KR + US 혼합)