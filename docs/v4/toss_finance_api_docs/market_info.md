매수 유의사항 조회​Copy link
종목의 매수 유의사항 및 변동성 완화(VI) 발동 정보를 조회합니다.

포함 종류: 정리매매(LIQUIDATION_TRADING), 단기과열종목(OVERHEATED), 투자경고(INVESTMENT_WARNING), 투자위험(INVESTMENT_RISK), VI 정적/동적/혼합(VI_STATIC / VI_DYNAMIC / VI_STATIC_AND_DYNAMIC), 신주인수권(STOCK_WARRANTS). 전체 enum 은 StockWarning.warningType 참조.

"활성"의 시간 기준: 응답 시점 기준으로 startDate <= 오늘 <= endDate 인 항목 (또는 endDate 가 null 인 진행 중 항목).

응답 정렬: startDate 내림차순 (최근 발동된 항목부터). startDate 가 동일한 경우 정렬 순서는 보장되지 않습니다.

데이터 적시성: VI 발동/해제는 거래소 이벤트 발생 후 수 초 내 반영됩니다. 정리매매·단기과열·투자경고/위험 지정은 거래소 공시 기준 일배치로 반영됩니다.

미존재 vs 빈 배열:

종목 자체가 없으면 404 stock-not-found.
종목은 있으나 활성 유의사항이 없으면 200 OK + result: [].
Rate Limits Group: STOCK

Path Parameters
symbolCopy link to symbol
Type:string
Pattern:^[A-Za-z0-9.\-]+$
required
Examples
종목 심볼. KRX: 6자리 숫자 (예: 005930), US: 영문 티커 (예: AAPL). 영문 대/소문자, 숫자, '.', '-' 만 허용한다.

Responses

200
application/json
성공

성공 응답 envelope. 200 응답에 사용됩니다. 각 엔드포인트의 성공 응답 스키마는 allOf 로 본 스키마를 상속하며 result 를 구체 타입으로 specialize 합니다. 실패 응답은 별도의 ErrorResponse 스키마를 사용합니다 (4xx/5xx). result 와 error 는 동시에 나타나지 않습니다.

resultCopy link to result
Type:array object[] · StockWarning[]
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
warningType
Type:string
enum
required
Example
유의사항 유형. 클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

값	의미
LIQUIDATION_TRADING	정리매매 (상장폐지 절차 진행 중)
OVERHEATED	단기과열종목 지정
INVESTMENT_WARNING	투자경고종목 지정
INVESTMENT_RISK	투자위험종목 지정
VI_STATIC_AND_DYNAMIC	변동성 완화장치(VI) 정적 + 동적 동시 발동
VI_STATIC	변동성 완화장치(VI) 정적 발동
VI_DYNAMIC	변동성 완화장치(VI) 동적 발동
STOCK_WARRANTS	신주인수권증서/증권
values
LIQUIDATION_TRADING
OVERHEATED
INVESTMENT_WARNING
INVESTMENT_RISK
VI_STATIC_AND_DYNAMIC
VI_STATIC
VI_DYNAMIC
STOCK_WARRANTS
endDate
Type:string | null
Format:date
Example
적용 종료일 (inclusive, YYYY-MM-DD, KST 기준). 진행 중이거나 미정 시 null

exchange
Type:string | null
Example
거래소 코드 (KRX, NXT 등 물리적 거래소 단위). stocks API의 market(상장 시장 단위)과 추상화 수준이 다름. 거래소 무관 경고는 null

startDate
Type:string | null
Format:date
Example
적용 시작일 (inclusive, YYYY-MM-DD, KST 기준). 시작일 미정 시 null


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

403
application/json
권한 부족

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
종목 심볼 조회 중 일시적 오류

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
Request Example forget/api/v1/stocks/{symbol}/warnings
Shell Curl
curl https://openapi.tossinvest.com/api/v1/stocks/005930/warnings \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:401
Status:403
Status:404
Status:429
Status:500
{
  "result": [
    {
      "warningType": "OVERHEATED",
      "exchange": "KRX",
      "startDate": "2026-03-20",
      "endDate": "2026-03-27"
    },
    {
      "warningType": "VI_STATIC",
      "exchange": "KRX",
      "startDate": "2026-03-26",
      "endDate": null
    }
  ]
}


유의사항이 있는 종목

국내 장 운영 정보 조회​Copy link
국내 시장의 거래 가능 시간을 조회합니다. 통합 모드 (KRX+NXT) 기준이며, 특수장(시간외종가/시간외단일가)은 제외됩니다. 전일/당일/익일 3영업일 정보를 반환합니다. 모든 시간은 KST(+09:00) 기준.

Rate Limits Group: MARKET_INFO

Query Parameters
dateCopy link to date
Type:string
Format:date
Example
조회 기준일 (YYYY-MM-DD)

Responses

200
application/json
성공

성공 응답 envelope. 200 응답에 사용됩니다. 각 엔드포인트의 성공 응답 스키마는 allOf 로 본 스키마를 상속하며 result 를 구체 타입으로 specialize 합니다. 실패 응답은 별도의 ErrorResponse 스키마를 사용합니다 (4xx/5xx). result 와 error 는 동시에 나타나지 않습니다.

resultCopy link to result
Type:object · KrMarketCalendarResponse
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
nextBusinessDay
Type:object · KrMarketDay
required
Hide Child Attributesfor nextBusinessDay
date
Type:string
Format:date
required
Example
영업일 (KST 기준)

integrated
Type:object · IntegratedHour
nullable
거래 가능 시간. 특수장(시간외종가/시간외단일가) 제외, 통합 모드 (KRX+NXT) 기준. 세 세션(preMarket, regularMarket, afterMarket) 각각 nullable. 해당 세션이 휴장이면 null, 세 세션 모두 null 이면 상위 integrated 자체가 null.

Hide Child Attributesfor integrated
afterMarket
Type:object · AfterMarketSession
nullable
애프터마켓 세션 (NXT)

Hide Child Attributesfor afterMarket
endTime
Type:string
Format:date-time
required
Example
애프터마켓 전체 종료

startTime
Type:string
Format:date-time
required
Example
애프터마켓 시작

singlePriceAuctionEndTime
Type:string
Format:date-time
nullable
Example
애프터마켓 내 시가단일가 구간 종료.

preMarket
Type:object · PreMarketSession
nullable
프리마켓 세션

Hide Child Attributesfor preMarket
endTime
Type:string
Format:date-time
required
Example
프리마켓 종료 (시가단일가 종료)

startTime
Type:string
Format:date-time
required
Example
프리마켓 시작

singlePriceAuctionStartTime
Type:string
Format:date-time
nullable
Example
프리마켓 내 시가단일가 구간 시작 (NXT 프리마켓 접속매매 종료). 단일가 정보 결손 시 null

regularMarket
Type:object · RegularMarketSession
nullable
정규장 세션. KRX·NXT 정규장의 합집합(가장 이른 시작 ~ 가장 늦은 종료). 종가단일가 구간을 포함

Hide Child Attributesfor regularMarket
endTime
Type:string
Format:date-time
required
Example
정규장 종료 (종가단일가 종료)

startTime
Type:string
Format:date-time
required
Example
정규장 시작. 가장 이른 KRX/NXT 정규장 시작 시각

singlePriceAuctionStartTime
Type:string
Format:date-time
nullable
Example
정규장 내 종가단일가 구간 시작 (KRX 기준). KRX 휴장이면 null

previousBusinessDay
Type:object · KrMarketDay
required
Hide Child Attributesfor previousBusinessDay
date
Type:string
Format:date
required
Example
영업일 (KST 기준)

integrated
Type:object · IntegratedHour
nullable
거래 가능 시간. 특수장(시간외종가/시간외단일가) 제외, 통합 모드 (KRX+NXT) 기준. 세 세션(preMarket, regularMarket, afterMarket) 각각 nullable. 해당 세션이 휴장이면 null, 세 세션 모두 null 이면 상위 integrated 자체가 null.

Hide Child Attributesfor integrated
afterMarket
Type:object · AfterMarketSession
nullable
애프터마켓 세션 (NXT)

Hide Child Attributesfor afterMarket
endTime
Type:string
Format:date-time
required
Example
애프터마켓 전체 종료

startTime
Type:string
Format:date-time
required
Example
애프터마켓 시작

singlePriceAuctionEndTime
Type:string
Format:date-time
nullable
Example
애프터마켓 내 시가단일가 구간 종료.

preMarket
Type:object · PreMarketSession
nullable
프리마켓 세션

Hide Child Attributesfor preMarket
endTime
Type:string
Format:date-time
required
Example
프리마켓 종료 (시가단일가 종료)

startTime
Type:string
Format:date-time
required
Example
프리마켓 시작

singlePriceAuctionStartTime
Type:string
Format:date-time
nullable
Example
프리마켓 내 시가단일가 구간 시작 (NXT 프리마켓 접속매매 종료). 단일가 정보 결손 시 null

regularMarket
Type:object · RegularMarketSession
nullable
정규장 세션. KRX·NXT 정규장의 합집합(가장 이른 시작 ~ 가장 늦은 종료). 종가단일가 구간을 포함

Hide Child Attributesfor regularMarket
endTime
Type:string
Format:date-time
required
Example
정규장 종료 (종가단일가 종료)

startTime
Type:string
Format:date-time
required
Example
정규장 시작. 가장 이른 KRX/NXT 정규장 시작 시각

singlePriceAuctionStartTime
Type:string
Format:date-time
nullable
Example
정규장 내 종가단일가 구간 시작 (KRX 기준). KRX 휴장이면 null

today
Type:object · KrMarketDay
required
Hide Child Attributesfor today
date
Type:string
Format:date
required
Example
영업일 (KST 기준)

integrated
Type:object · IntegratedHour
nullable
거래 가능 시간. 특수장(시간외종가/시간외단일가) 제외, 통합 모드 (KRX+NXT) 기준. 세 세션(preMarket, regularMarket, afterMarket) 각각 nullable. 해당 세션이 휴장이면 null, 세 세션 모두 null 이면 상위 integrated 자체가 null.

Hide Child Attributesfor integrated
afterMarket
Type:object · AfterMarketSession
nullable
애프터마켓 세션 (NXT)

Hide Child Attributesfor afterMarket
endTime
Type:string
Format:date-time
required
Example
애프터마켓 전체 종료

startTime
Type:string
Format:date-time
required
Example
애프터마켓 시작

singlePriceAuctionEndTime
Type:string
Format:date-time
nullable
Example
애프터마켓 내 시가단일가 구간 종료.

preMarket
Type:object · PreMarketSession
nullable
프리마켓 세션

Hide Child Attributesfor preMarket
endTime
Type:string
Format:date-time
required
Example
프리마켓 종료 (시가단일가 종료)

startTime
Type:string
Format:date-time
required
Example
프리마켓 시작

singlePriceAuctionStartTime
Type:string
Format:date-time
nullable
Example
프리마켓 내 시가단일가 구간 시작 (NXT 프리마켓 접속매매 종료). 단일가 정보 결손 시 null

regularMarket
Type:object · RegularMarketSession
nullable
정규장 세션. KRX·NXT 정규장의 합집합(가장 이른 시작 ~ 가장 늦은 종료). 종가단일가 구간을 포함

Hide Child Attributesfor regularMarket
endTime
Type:string
Format:date-time
required
Example
정규장 종료 (종가단일가 종료)

startTime
Type:string
Format:date-time
required
Example
정규장 시작. 가장 이른 KRX/NXT 정규장 시작 시각

singlePriceAuctionStartTime
Type:string
Format:date-time
nullable
Example
정규장 내 종가단일가 구간 시작 (KRX 기준). KRX 휴장이면 null


400
application/json
잘못된 요청

Type:object · ErrorResponse
Example
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
시장 정보 조회 중 일시적 오류

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
Request Example forget/api/v1/market-calendar/KR
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/market-calendar/KR?date=2026-03-25' \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:400
Status:429
Status:500
{
  "result": {
    "today": {
      "date": "2026-03-25",
      "integrated": {
        "preMarket": {
          "startTime": "2026-03-25T08:00:00+09:00",
          "singlePriceAuctionStartTime": "2026-03-25T08:50:00+09:00",
          "endTime": "2026-03-25T09:00:00+09:00"
        },
        "regularMarket": {
          "startTime": "2026-03-25T09:00:00+09:00",
          "singlePriceAuctionStartTime": "2026-03-25T15:20:00+09:00",
          "endTime": "2026-03-25T15:30:00+09:00"
        },
        "afterMarket": {
          "startTime": "2026-03-25T15:30:00+09:00",
          "singlePriceAuctionEndTime": "2026-03-25T15:40:00+09:00",
          "endTime": "2026-03-25T20:00:00+09:00"
        }
      }
    },
    "previousBusinessDay": {
      "date": "2026-03-24",
      "integrated": {
        "preMarket": {
          "startTime": "2026-03-24T08:00:00+09:00",
          "singlePriceAuctionStartTime": "2026-03-24T08:50:00+09:00",
          "endTime": "2026-03-24T09:00:00+09:00"
        },
        "regularMarket": {
          "startTime": "2026-03-24T09:00:00+09:00",
          "singlePriceAuctionStartTime": "2026-03-24T15:20:00+09:00",
          "endTime": "2026-03-24T15:30:00+09:00"
        },
        "afterMarket": {
          "startTime": "2026-03-24T15:30:00+09:00",
          "singlePriceAuctionEndTime": "2026-03-24T15:40:00+09:00",
          "endTime": "2026-03-24T20:00:00+09:00"
        }
      }
    },
    "nextBusinessDay": {
      "date": "2026-03-26",
      "integrated": {
        "preMarket": {
          "startTime": "2026-03-26T08:00:00+09:00",
          "singlePriceAuctionStartTime": "2026-03-26T08:50:00+09:00",
          "endTime": "2026-03-26T09:00:00+09:00"
        },
        "regularMarket": {
          "startTime": "2026-03-26T09:00:00+09:00",
          "singlePriceAuctionStartTime": "2026-03-26T15:20:00+09:00",
          "endTime": "2026-03-26T15:30:00+09:00"
        },
        "afterMarket": {
          "startTime": "2026-03-26T15:30:00+09:00",
          "singlePriceAuctionEndTime": "2026-03-26T15:40:00+09:00",
          "endTime": "2026-03-26T20:00:00+09:00"
        }
      }
    }
  }
}


영업일 (KRX+NXT 정상 운영)


해외 장 운영 정보 조회​Copy link
미국 시장의 장 운영 시간을 조회합니다. 4 세션(dayMarket, preMarket, regularMarket, afterMarket) 별로 nullable. 휴장 시 4 세션 모두 null. 전일/당일/익일 3영업일 정보를 반환합니다. 모든 시간은 KST(+09:00) 기준.

Rate Limits Group: MARKET_INFO

Query Parameters
dateCopy link to date
Type:string
Format:date
Example
조회 기준일 (YYYY-MM-DD, 미국 현지 날짜)

Responses

200
application/json
성공

성공 응답 envelope. 200 응답에 사용됩니다. 각 엔드포인트의 성공 응답 스키마는 allOf 로 본 스키마를 상속하며 result 를 구체 타입으로 specialize 합니다. 실패 응답은 별도의 ErrorResponse 스키마를 사용합니다 (4xx/5xx). result 와 error 는 동시에 나타나지 않습니다.

resultCopy link to result
Type:object · UsMarketCalendarResponse
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
nextBusinessDay
Type:object · UsMarketDay
required
미국 시장 영업일 정보. 4 세션(dayMarket, preMarket, regularMarket, afterMarket) 각각 nullable. 휴장일이면 4 세션 모두 null.

Hide Child Attributesfor nextBusinessDay
date
Type:string
Format:date
required
Example
영업일 (미국 현지 기준)

afterMarket
Type:object · UsAfterMarketSession
nullable
애프터마켓 세션

Hide Child Attributesfor afterMarket
endTime
Type:string
Format:date-time
required
Example
애프터마켓 종료

startTime
Type:string
Format:date-time
required
Example
애프터마켓 시작

dayMarket
Type:object · UsDayMarketSession
nullable
데이마켓 세션 (토스증권)

Hide Child Attributesfor dayMarket
endTime
Type:string
Format:date-time
required
Example
데이마켓 종료

startTime
Type:string
Format:date-time
required
Example
데이마켓 시작

preMarket
Type:object · UsPreMarketSession
nullable
프리마켓 세션

Hide Child Attributesfor preMarket
endTime
Type:string
Format:date-time
required
Example
프리마켓 종료

startTime
Type:string
Format:date-time
required
Example
프리마켓 시작

regularMarket
Type:object · UsRegularMarketSession
nullable
정규장 세션

Hide Child Attributesfor regularMarket
endTime
Type:string
Format:date-time
required
Example
정규장 종료

startTime
Type:string
Format:date-time
required
Example
정규장 시작

previousBusinessDay
Type:object · UsMarketDay
required
미국 시장 영업일 정보. 4 세션(dayMarket, preMarket, regularMarket, afterMarket) 각각 nullable. 휴장일이면 4 세션 모두 null.

Hide Child Attributesfor previousBusinessDay
date
Type:string
Format:date
required
Example
영업일 (미국 현지 기준)

afterMarket
Type:object · UsAfterMarketSession
nullable
애프터마켓 세션

Hide Child Attributesfor afterMarket
endTime
Type:string
Format:date-time
required
Example
애프터마켓 종료

startTime
Type:string
Format:date-time
required
Example
애프터마켓 시작

dayMarket
Type:object · UsDayMarketSession
nullable
데이마켓 세션 (토스증권)

Hide Child Attributesfor dayMarket
endTime
Type:string
Format:date-time
required
Example
데이마켓 종료

startTime
Type:string
Format:date-time
required
Example
데이마켓 시작

preMarket
Type:object · UsPreMarketSession
nullable
프리마켓 세션

Hide Child Attributesfor preMarket
endTime
Type:string
Format:date-time
required
Example
프리마켓 종료

startTime
Type:string
Format:date-time
required
Example
프리마켓 시작

regularMarket
Type:object · UsRegularMarketSession
nullable
정규장 세션

Hide Child Attributesfor regularMarket
endTime
Type:string
Format:date-time
required
Example
정규장 종료

startTime
Type:string
Format:date-time
required
Example
정규장 시작

today
Type:object · UsMarketDay
required
미국 시장 영업일 정보. 4 세션(dayMarket, preMarket, regularMarket, afterMarket) 각각 nullable. 휴장일이면 4 세션 모두 null.

Hide Child Attributesfor today
date
Type:string
Format:date
required
Example
영업일 (미국 현지 기준)

afterMarket
Type:object · UsAfterMarketSession
nullable
애프터마켓 세션

Hide Child Attributesfor afterMarket
endTime
Type:string
Format:date-time
required
Example
애프터마켓 종료

startTime
Type:string
Format:date-time
required
Example
애프터마켓 시작

dayMarket
Type:object · UsDayMarketSession
nullable
데이마켓 세션 (토스증권)

Hide Child Attributesfor dayMarket
endTime
Type:string
Format:date-time
required
Example
데이마켓 종료

startTime
Type:string
Format:date-time
required
Example
데이마켓 시작

preMarket
Type:object · UsPreMarketSession
nullable
프리마켓 세션

Hide Child Attributesfor preMarket
endTime
Type:string
Format:date-time
required
Example
프리마켓 종료

startTime
Type:string
Format:date-time
required
Example
프리마켓 시작

regularMarket
Type:object · UsRegularMarketSession
nullable
정규장 세션

Hide Child Attributesfor regularMarket
endTime
Type:string
Format:date-time
required
Example
정규장 종료

startTime
Type:string
Format:date-time
required
Example
정규장 시작


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
시장 정보 조회 중 일시적 오류

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
Request Example forget/api/v1/market-calendar/US
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/market-calendar/US?date=2026-03-25' \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:429
Status:500
{
  "result": {
    "today": {
      "date": "2026-03-25",
      "dayMarket": {
        "startTime": "2026-03-25T09:00:00+09:00",
        "endTime": "2026-03-25T16:50:00+09:00"
      },
      "preMarket": {
        "startTime": "2026-03-25T17:00:00+09:00",
        "endTime": "2026-03-25T22:30:00+09:00"
      },
      "regularMarket": {
        "startTime": "2026-03-25T22:30:00+09:00",
        "endTime": "2026-03-26T05:00:00+09:00"
      },
      "afterMarket": {
        "startTime": "2026-03-26T05:00:00+09:00",
        "endTime": "2026-03-26T07:00:00+09:00"
      }
    },
    "previousBusinessDay": {
      "date": "2026-03-24",
      "dayMarket": {
        "startTime": "2026-03-24T09:00:00+09:00",
        "endTime": "2026-03-24T16:50:00+09:00"
      },
      "preMarket": {
        "startTime": "2026-03-24T17:00:00+09:00",
        "endTime": "2026-03-24T22:30:00+09:00"
      },
      "regularMarket": {
        "startTime": "2026-03-24T22:30:00+09:00",
        "endTime": "2026-03-25T05:00:00+09:00"
      },
      "afterMarket": {
        "startTime": "2026-03-25T05:00:00+09:00",
        "endTime": "2026-03-25T07:00:00+09:00"
      }
    },
    "nextBusinessDay": {
      "date": "2026-03-26",
      "dayMarket": {
        "startTime": "2026-03-26T09:00:00+09:00",
        "endTime": "2026-03-26T16:50:00+09:00"
      },
      "preMarket": {
        "startTime": "2026-03-26T17:00:00+09:00",
        "endTime": "2026-03-26T22:30:00+09:00"
      },
      "regularMarket": {
        "startTime": "2026-03-26T22:30:00+09:00",
        "endTime": "2026-03-27T05:00:00+09:00"
      },
      "afterMarket": {
        "startTime": "2026-03-27T05:00:00+09:00",
        "endTime": "2026-03-27T07:00:00+09:00"
      }
    }
  }
}


영업일 (데이마켓 포함, 4 세션 nested)


