Market Data (Collapsed)​Copy link
종목의 실시간성 시세 정보를 조회하는 그룹입니다. 매수/매도 호가, 현재가, 최근 체결 내역, 상·하한가, 캔들 차트(1분봉·일봉)를 제공합니다. 계좌 정보 없이 액세스 토큰만으로 호출할 수 있습니다. 호가·현재가·체결·상하한가는 MARKET_DATA Rate Limits Group 에 속하고, 캔들 차트는 호출 부하 특성이 달라 별도의 MARKET_DATA_CHART Rate Limits Group 으로 관리되므로, 두 그룹의 한도 응답 헤더를 각각 확인하는 것을 권장합니다.

이용 안내

웹 소켓은 추후 지원 예정입니다
호가 조회​Copy link
매수/매도 호가 및 잔량을 조회합니다.

Rate Limits Group: MARKET_DATA

Query Parameters
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
Type:object · OrderbookResponse
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
asks
Type:array object[] · OrderbookEntry[]
required
매도호가 목록 (낮은 가격순)

Show Child Attributesfor asks
bids
Type:array object[] · OrderbookEntry[]
required
매수호가 목록 (높은 가격순)

Show Child Attributesfor bids
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
timestamp
Type:string | null
Format:date-time
Example
데이터 시각. 데이터 미제공 시 null


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
시세 조회 중 일시적 오류

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
Request Example forget/api/v1/orderbook
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/orderbook?symbol=005930' \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:404
Status:429
Status:500
{
  "result": {
    "timestamp": "2026-03-25T09:30:00.123+09:00",
    "currency": "KRW",
    "asks": [
      {
        "price": "72300",
        "volume": "1200"
      },
      {
        "price": "72200",
        "volume": "3400"
      },
      {
        "price": "72100",
        "volume": "8500"
      }
    ],
    "bids": [
      {
        "price": "72000",
        "volume": "5200"
      },
      {
        "price": "71900",
        "volume": "4100"
      },
      {
        "price": "71800",
        "volume": "2700"
      }
    ]
  }
}


국내 주식 (삼성전자)
성공



현재가 조회​Copy link
종목의 현재가 정보를 조회합니다. 최대 200건 까지 다건 조회를 지원하며 콤마(,)로 구분합니다.

Rate Limits Group: MARKET_DATA

Query Parameters
symbolsCopy link to symbols
Type:string
Pattern:^[A-Za-z0-9.,\-]+$
required
Example
종목 심볼. 최대 200 개를 콤마(,)로 구분. 예: 005930,000660 또는 AAPL,MSFT. 영문 대/소문자, 숫자, '.', '-' 만 허용한다.

Responses

200
application/json
성공

성공 응답 envelope. 200 응답에 사용됩니다. 각 엔드포인트의 성공 응답 스키마는 allOf 로 본 스키마를 상속하며 result 를 구체 타입으로 specialize 합니다. 실패 응답은 별도의 ErrorResponse 스키마를 사용합니다 (4xx/5xx). result 와 error 는 동시에 나타나지 않습니다.

resultCopy link to result
Type:array object[] · PriceResponse[]
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
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
lastPrice
Type:string
max length:  
30
Format:decimal
required
Example
현재가

symbol
Type:string
required
Example
종목 심볼

timestamp
Type:string | null
Format:date-time
Example
데이터 시각. 체결 미발생 등으로 시각이 없을 경우 null


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

Show Child Attributesfor data

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

Show Child Attributesfor data

500
application/json
시세 조회 중 일시적 오류

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



최근 체결 내역 조회​Copy link
당일 최근 체결 내역을 조회합니다.

Rate Limits Group: MARKET_DATA

Query Parameters
symbolCopy link to symbol
Type:string
Pattern:^[A-Za-z0-9.\-]+$
required
Examples
종목 심볼. KRX: 6자리 숫자 (예: 005930), US: 영문 티커 (예: AAPL). 영문 대/소문자, 숫자, '.', '-' 만 허용한다.

countCopy link to count
Type:integer
min:  
1
max:  
50
Default
조회 건수 (최대 50)

Responses

200
application/json
성공

성공 응답 envelope. 200 응답에 사용됩니다. 각 엔드포인트의 성공 응답 스키마는 allOf 로 본 스키마를 상속하며 result 를 구체 타입으로 specialize 합니다. 실패 응답은 별도의 ErrorResponse 스키마를 사용합니다 (4xx/5xx). result 와 error 는 동시에 나타나지 않습니다.

resultCopy link to result
Type:array object[] · Trade[]
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
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
price
Type:string
max length:  
30
Format:decimal
required
Example
체결가

timestamp
Type:string
Format:date-time
required
Example
체결 시각

volume
Type:string
max length:  
30
Format:decimal
required
Example
체결 수량


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

Show Child Attributesfor data

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
시세 조회 중 일시적 오류

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
Request Example forget/api/v1/trades
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/trades?symbol=005930&count=50' \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:404
Status:429
Status:500
{
  "result": [
    {
      "price": "72000",
      "volume": "120",
      "timestamp": "2026-03-25T09:30:42.000+09:00",
      "currency": "KRW"
    },
    {
      "price": "71900",
      "volume": "50",
      "timestamp": "2026-03-25T09:30:41.500+09:00",
      "currency": "KRW"
    },
    {
      "price": "72000",
      "volume": "200",
      "timestamp": "2026-03-25T09:30:40.800+09:00",
      "currency": "KRW"
    }
  ]
}


국내 주식 (삼성전자)

상/하한가 조회​Copy link
종목의 당일 상한가 및 하한가를 조회합니다.

Rate Limits Group: MARKET_DATA

Query Parameters
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
Type:object · PriceLimitResponse
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
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
timestamp
Type:string
Format:date-time
required
Example
데이터 시각

lowerLimitPrice
Type:string
max length:  
30
Format:decimal
Example
하한가. 미국 주식 등 가격제한이 없는 시장에서는 null

upperLimitPrice
Type:string
max length:  
30
Format:decimal
Example
상한가. 미국 주식 등 가격제한이 없는 시장에서는 null


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

Show Child Attributesfor data

500
application/json
시세 조회 중 일시적 오류

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

Show Child Attributesfor data
Request Example forget/api/v1/price-limits
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/price-limits?symbol=005930' \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:404
Status:429
Status:500
{
  "result": {
    "timestamp": "2026-03-25T09:30:00.123+09:00",
    "upperLimitPrice": "93000",
    "lowerLimitPrice": "50400",
    "currency": "KRW"
  }
}


국내 주식 (삼성전자)

캔들 차트 조회​Copy link
종목의 캔들(OHLCV) 차트 데이터를 조회합니다. 최대 200개 봉을 반환합니다.

Rate Limits Group: MARKET_DATA_CHART

Query Parameters
symbolCopy link to symbol
Type:string
Pattern:^[A-Za-z0-9.\-]+$
required
Examples
종목 심볼. KRX: 6자리 숫자 (예: 005930), US: 영문 티커 (예: AAPL). 영문 대/소문자, 숫자, '.', '-' 만 허용한다.

intervalCopy link to interval
Type:string
enum
required
봉 단위

values
1m
1d
countCopy link to count
Type:integer
min:  
1
max:  
200
Default
조회 봉 수 (최대 200)

beforeCopy link to before
Type:string
Format:date-time
Example
페이지네이션 상한 (exclusive, ISO 8601). 이 시각보다 이전의 봉만 반환합니다. 미지정 시 가장 최신 봉부터 반환. 다음 페이지 요청 시 이전 응답의 nextBefore 값을 그대로 전달합니다.

adjustedCopy link to adjusted
Type:boolean
Default
수정주가 적용 여부. true 면 수정주가 적용, false 면 미적용.

Responses

200
application/json
성공

성공 응답 envelope. 200 응답에 사용됩니다. 각 엔드포인트의 성공 응답 스키마는 allOf 로 본 스키마를 상속하며 result 를 구체 타입으로 specialize 합니다. 실패 응답은 별도의 ErrorResponse 스키마를 사용합니다 (4xx/5xx). result 와 error 는 동시에 나타나지 않습니다.

resultCopy link to result
Type:object · CandlePageResponse
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
candles
Type:array object[] · Candle[]
required
캔들 목록

Hide Child Attributesfor candles
closePrice
Type:string
max length:  
30
Format:decimal
required
Example
종가

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
highPrice
Type:string
max length:  
30
Format:decimal
required
Example
고가

lowPrice
Type:string
max length:  
30
Format:decimal
required
Example
저가

openPrice
Type:string
max length:  
30
Format:decimal
required
Example
시가

timestamp
Type:string
Format:date-time
required
Example
봉 시작 시각

volume
Type:string
max length:  
30
Format:decimal
required
Example
거래량

nextBefore
Type:string | null
Format:date-time
다음 페이지 조회 시 before 쿼리 파라미터에 그대로 전달. 마지막 페이지면 null.


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
시세 조회 중 일시적 오류

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

Show Child Attributesfor data
Request Example forget/api/v1/candles
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/candles?symbol=005930&interval=1m&count=100&before=2026-03-25T09%3A00%3A00%2B09%3A00&adjusted=true' \
  --header 'Authorization: Bearer YOUR_SECRET_TOKEN'

Status:200
Status:400
Status:404
Status:429
Status:500
{
  "result": {
    "candles": [
      {
        "timestamp": "2026-03-25T09:00:00+09:00",
        "openPrice": "71600",
        "highPrice": "72300",
        "lowPrice": "71500",
        "closePrice": "72000",
        "volume": "3521000",
        "currency": "KRW"
      },
      {
        "timestamp": "2026-03-24T09:00:00+09:00",
        "openPrice": "71200",
        "highPrice": "71800",
        "lowPrice": "71000",
        "closePrice": "71600",
        "volume": "2984000",
        "currency": "KRW"
      }
    ],
    "nextBefore": "2026-03-24T09:00:00+09:00"
  }
}


일봉 (1d)



