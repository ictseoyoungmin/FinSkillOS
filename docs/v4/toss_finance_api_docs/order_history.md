Order History (Collapsed)​Copy link
제출한 주문의 처리 상태와 체결 내역을 조회하는 그룹입니다. status 파라미터로 라이프사이클 그룹(현재 진행 중 주문 OPEN)을 선택해 주문 목록을 조회하고, 개별 orderId로 모든 상태의 주문 상세를 조회할 수 있습니다. 상세 조회는 부분 체결 내역 등 주문 단위 정보를 포함합니다. 호출 시 X-Tossinvest-Account 헤더가 필요합니다.

주문 목록 조회​Copy link
주문 목록을 조회합니다. status 파라미터로 주문 상태를 필터링합니다.

지원하는 status 값:

진행 중 주문: OPEN -- PENDING, PARTIAL_FILLED, PENDING_CANCEL, PENDING_REPLACE 상태의 주문을 반환
종료된 주문: CLOSED -- 현재 호출 시 400 closed-not-supported 를 반환합니다.
symbol을 지정하면 해당 종목의 주문만 필터링하여 반환합니다.

페이징 동작:

status=OPEN: 모든 대기 중 주문을 전량 반환합니다. limit, cursor 는 무시되며, from/to 만 주문 생성일(orderedAt, KST 기준) 범위 필터로 적용됩니다 (미지정 시 전체 기간).
status=CLOSED: 미지원. cursor, limit, from, to 파라미터는 현재 효과가 없습니다.
Rate Limits Group: ORDER_HISTORY

Query Parameters
statusCopy link to status
Type:string
enum
required
Example
주문 라이프사이클 그룹 필터. 이 값은 각 주문의 세부 상태(orders[].status)를 그룹화한 라벨이며, orders[].status 와 값 체계가 다릅니다.

OPEN: 진행 중 주문 그룹 — orders[].status ∈ {PENDING, PARTIAL_FILLED, PENDING_CANCEL, PENDING_REPLACE}
CLOSED: 종료된 주문 그룹. 현재 호출 시 400 closed-not-supported 를 반환합니다.
예: status=OPEN 을 요청하면 응답의 orders[].status 는 개별 주문에 따라 PENDING, PARTIAL_FILLED, PENDING_CANCEL, PENDING_REPLACE 중 하나로 내려옵니다.

values
OPEN
CLOSED
symbolCopy link to symbol
Type:string
Pattern:^[A-Za-z0-9.\-]+$
Examples
종목 심볼. 지정 시 해당 종목의 주문만 조회. KRX: 6자리 숫자 (005930), US: 영문 티커 (AAPL). 영문 대/소문자, 숫자, '.', '-' 만 허용한다.

fromCopy link to from
Type:string
Format:date
Example
조회 시작일 (inclusive, KST 기준). 주문 생성 시간(orderedAt) 기준. 미지정 시 전체 기간. status=CLOSED 는 미지원이므로 현재 효과가 없습니다.

toCopy link to to
Type:string
Format:date
Example
조회 종료일 (inclusive, KST 기준). 주문 생성 시간(orderedAt) 기준. 미지정 시 전체 기간. status=CLOSED 는 미지원이므로 현재 효과가 없습니다.

cursorCopy link to cursor
Type:string
페이지네이션 커서. OPEN 에서는 무시되며, CLOSED 는 미지원이므로 현재 효과가 없습니다.

limitCopy link to limit
Type:integer
min:  
1
max:  
100
Default
페이지 크기. OPEN 에서는 무시됩니다 (전량 반환). CLOSED 는 미지원이므로 현재 효과가 없습니다.

Headers
X-Tossinvest-AccountCopy link to X-Tossinvest-Account
Type:integer
Format:int64
required
Example
API 요청 시 사용할 계좌의 accountSeq. GET /api/v1/accounts 응답의 accountSeq 값을 사용합니다.

Responses

200
성공
application/json

400
잘못된 요청
application/json

401
인증 실패. WWW-Authenticate: Bearer ... 헤더가 함께 내려갑니다.
application/json

404
종목을 찾을 수 없음
application/json

429
요청 한도 초과. 포함 헤더의 의미는 아래 headers 정의를 참조합니다.
application/json

500
주문 조회 중 일시적 오류
application/json
Request Example forget/api/v1/orders
Shell Curl
curl 'https://openapi.tossinvest.com/api/v1/orders?status=OPEN&symbol=005930&from=2026-03-01&to=2026-03-31&cursor=&limit=20' \
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
    "orders": [
      {
        "orderId": "bAGzNvMOOTa5Uy0xVzYNbxDJ3Qpobwau4jDF3hyZZGWbpHm7wha8CFZc7aXVOWAl",
        "symbol": "005930",
        "side": "BUY",
        "orderType": "LIMIT",
        "timeInForce": "DAY",
        "status": "PENDING",
        "price": "70000",
        "quantity": "10",
        "orderAmount": null,
        "currency": "KRW",
        "orderedAt": "2026-03-29T09:30:00+09:00",
        "canceledAt": null,
        "execution": {
          "filledQuantity": "0",
          "averageFilledPrice": null,
          "filledAmount": null,
          "commission": null,
          "tax": null,
          "filledAt": null,
          "settlementDate": null
        }
      },
      {
        "orderId": "RpP3_wtsiKe9btBvdendaHoBqOIY_Zb_xPkRfYaqCIvf2FXtMDv_mo7VnD7KB-ia",
        "symbol": "AAPL",
        "side": "SELL",
        "orderType": "LIMIT",
        "timeInForce": "DAY",
        "status": "PARTIAL_FILLED",
        "price": "185.5",
        "quantity": "5",
        "orderAmount": null,
        "currency": "USD",
        "orderedAt": "2026-03-29T10:00:00+09:00",
        "canceledAt": null,
        "execution": {
          "filledQuantity": "2",
          "averageFilledPrice": "185.25",
          "filledAmount": "370.5",
          "commission": "0.66",
          "tax": "0",
          "filledAt": "2026-03-29T10:00:05+09:00",
          "settlementDate": null
        }
      }
    ],
    "nextCursor": null,
    "hasNext": false
  }
}


대기중 주문 — 국내+해외 혼합 (전량 반환)
성공

주문 상세 조회​Copy link
특정 주문의 상세 정보를 조회합니다. 모든 주문 상태(체결 완료, 취소, 거부 등)의 주문을 조회할 수 있습니다.

Rate Limits Group: ORDER_HISTORY

Path Parameters
orderIdCopy link to orderId
Type:string
required
Example
주문 식별자. 서버에서 발급한 opaque token 입니다.

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
Type:object · Order
required
성공 응답의 페이로드. 엔드포인트별 타입이 다르며, 각 엔드포인트 스펙에서 allOf 로 구체 타입을 명시합니다.

Hide Child Attributesfor result
currency
Type:string · Currency
enum
required
Example
통화 코드.

KRW: 한국 원화
USD: 미국 달러
클라이언트는 unknown enum 값을 허용하도록 구현해야 합니다.

values
KRW
USD
execution
Type:object · OrderExecution
required
체결 결과. 체결 내역이 없으면 filledQuantity=0

Hide Child Attributesfor execution
averageFilledPrice
Type:string
max length:  
30
Format:decimal
required
Example
평균 체결 가격 (native currency). 부분 체결 시 체결된 건의 평균

commission
Type:string
max length:  
30
Format:decimal
required
Example
총 체결 수수료 (native currency)

filledAmount
Type:string
max length:  
30
Format:decimal
required
Example
총 체결 금액 (native currency)

filledAt
Type:string | null
Format:date-time
required
Example
최종 체결 시간 (ISO 8601, KST)

filledQuantity
Type:string
max length:  
30
Format:decimal
required
Example
체결 수량

settlementDate
Type:string | null
Format:date
required
Example
결제 예정일 (YYYY-MM-DD, KST 기준). 미결제 시 null

tax
Type:string
max length:  
30
Format:decimal
required
Example
총 체결 세금 (native currency)

orderedAt
Type:string
Format:date-time
required
Example
주문 시간 (ISO 8601, KST)

orderId
Type:string
required
Example
주문 식별자

orderType
Type:string
enum
required
Example
호가 유형.

LIMIT: 지정가
MARKET: 시장가
클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

values
LIMIT
MARKET
quantity
Type:string
max length:  
30
Format:decimal
required
Example
주문 수량

side
Type:string
enum
required
Example
주문 방향

values
BUY
SELL
status
Type:string · OrderStatus
enum
required
Example
주문 상태.

PENDING: 체결 대기. 주문이 접수되어 체결을 대기 중인 상태
PENDING_CANCEL: 취소 대기. 취소 요청이 접수되어 브로커 응답을 대기 중인 상태
PENDING_REPLACE: 정정 대기. 정정 요청이 접수되어 브로커 응답을 대기 중인 상태
PARTIAL_FILLED: 부분 체결. 주문 수량 중 일부만 체결된 상태
FILLED: 체결 완료. 주문 수량이 전량 체결된 상태
CANCELED: 취소 완료. execution.filledQuantity를 통해 부분 체결 여부를 확인할 수 있음
REJECTED: 거부됨. 브로커가 주문을 거부한 상태. execution.filledQuantity를 통해 부분 체결 여부를 확인할 수 있음
CANCEL_REJECTED: 취소 거부. 브로커가 취소 요청을 거부한 경우 별도 주문 레코드로 생성됨. 원주문은 이전 상태로 복귀함
REPLACE_REJECTED: 정정 거부. 브로커가 정정 요청을 거부한 경우 별도 주문 레코드로 생성됨. 원주문은 이전 상태로 복귀함
REPLACED: 정정됨. 정정 요청이 수락되어 원주문이 대체된 상태. execution.filledQuantity를 통해 부분 체결 여부를 확인할 수 있음
클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

values
PENDING
PENDING_CANCEL
PENDING_REPLACE
PARTIAL_FILLED
FILLED
CANCELED
REJECTED
CANCEL_REJECTED
REPLACE_REJECTED
REPLACED
Hide values
symbol
Type:string
required
Example
종목 심볼. KRX: 6자리 숫자, US: 영문 티커

timeInForce
Type:string
enum
required
Example
주문 유효 조건 (Time In Force). orderType 과 결합되어 주문 방식이 결정됩니다 (예: LIMIT + CLS = LOC).

DAY: 당일 유효 (Day)
CLS: 장 마감 주문 (At the Close)
OPG: 장 개시 주문 (At the Opening). 현재는 지원하지 않습니다.
클라이언트는 unknown code 를 허용하도록 구현해야 합니다.

values
DAY
CLS
OPG
canceledAt
Type:string | null
Format:date-time
취소 시간 (ISO 8601, KST). 해당 없으면 null

orderAmount
Type:string
max length:  
30
Format:decimal
주문 금액 (USD). 금액 기반 US 시장가 매수 주문에만 해당. 그 외 null

price
Type:string
max length:  
30
Format:decimal
Example
주문 가격 (native currency). MARKET 주문 시 null


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
주문을 찾을 수 없음

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
주문 조회 중 일시적 오류

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
Request Example forget/api/v1/orders/{orderId}
Shell Curl
curl https://openapi.tossinvest.com/api/v1/orders/0d5QIHjmtksbsmM-hBRAgP-ExI8iodGm9fAR5txelPfnMM8XQ_swoJdwL5RpGWMo \
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
    "orderId": "J4lDkgVA-pMiRPOqXd2nBjxTj8hsTVhzOhIth7i1Izq14XYxIg1r_QTDEH7RTL8d",
    "symbol": "AAPL",
    "side": "BUY",
    "orderType": "MARKET",
    "timeInForce": "DAY",
    "status": "PARTIAL_FILLED",
    "price": null,
    "quantity": "5",
    "orderAmount": null,
    "currency": "USD",
    "orderedAt": "2026-03-28T23:30:00+09:00",
    "canceledAt": null,
    "execution": {
      "filledQuantity": "3",
      "averageFilledPrice": "185.25",
      "filledAmount": "555.75",
      "commission": "0.99",
      "tax": "0",
      "filledAt": "2026-03-28T23:30:05+09:00",
      "settlementDate": null
    }
  }
}


해외주식 시장가 매수 — 부분 체결