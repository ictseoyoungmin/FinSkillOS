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


