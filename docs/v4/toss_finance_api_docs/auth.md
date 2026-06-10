Auth (Collapsed)​Copy link
토스증권 Open API의 모든 요청에 필요한 액세스 토큰을 발급하는 그룹입니다. OAuth 2.0 Client Credentials Grant 방식으로 client_id·client_secret을 토큰으로 교환하며, 발급된 토큰은 이후 모든 API의 Authorization: Bearer 헤더에 사용됩니다. 이 그룹의 엔드포인트만 Authorization 헤더 없이 호출하며, 응답은 BFF 공통 envelope이 아닌 OAuth 2.0 표준 형식을 따릅니다.

OAuth2 액세스 토큰 발급​Copy link
OAuth 2.0 Client Credentials Grant 로 access token 을 발급합니다.

요청 본문은 application/x-www-form-urlencoded 으로 전송합니다.
발급된 token 은 다른 모든 API 의 Authorization: Bearer {access_token} 헤더에 사용합니다.
응답 형식은 BFF 공통 envelope 이 아닌 OAuth2 표준 형식을 따릅니다.
refresh token 은 제공되지 않습니다. 만료 시 동일 엔드포인트로 재발급합니다.
client 당 유효한 access token 은 1 개입니다. 재발급 시 이전에 발급된 token 은 즉시 무효화됩니다.
Rate Limits Group: AUTH

Body
·OAuth2TokenRequest
required
application/x-www-form-urlencoded
OAuth2 Client Credentials Grant 토큰 발급 요청. application/x-www-form-urlencoded 으로 전송합니다.

client_idCopy link to client_id
Type:string
required
Example
발급받은 클라이언트 ID

client_secretCopy link to client_secret
Type:string
Format:password
required
발급받은 클라이언트 시크릿. 노출되지 않도록 서버 측에서만 사용합니다.

grant_typeCopy link to grant_type
enum
const:  
client_credentials
required
인증 방식. client_credentials 만 지원합니다.

values
client_credentials
Responses

200
application/json
토큰 발급 성공

Type:object · OAuth2TokenResponse
토큰 발급 성공 응답. BFF 의 공통 ApiResponse envelope 을 사용하지 않고 OAuth2 표준 형식으로 응답합니다.

access_token
Type:string
required
Example
JWT 형식의 access token. 모든 API 요청의 Authorization: Bearer 헤더에 담습니다.

expires_in
Type:integer
Format:int64
required
Example
토큰 만료까지 남은 초.

token_type
enum
const:  
Bearer
required
Example
토큰 타입. 항상 Bearer.

values
Bearer

400
application/json
잘못된 요청. 필수 파라미터 누락, 지원하지 않는 grant_type 등.

Type:object · OAuth2ErrorResponse
Examples
OAuth2 토큰 발급 실패 응답. /oauth2/token 엔드포인트는 BFF 공통 ErrorResponse envelope 이 아닌 OAuth2 표준 포맷으로 응답합니다. 클라이언트는 code 가 아닌 error 필드로 에러를 식별해야 합니다.

error
Type:string
enum
required
에러 코드.

values
invalid_request
invalid_client
invalid_grant
unauthorized_client
unsupported_grant_type
error_description
Type:string
Example
에러 상세 설명 (선택). 메시지에 non-ASCII 문자가 포함되는 경우 생략될 수 있습니다.

error_uri
Type:string
Format:uri
에러 정보가 게시된 페이지 URI (선택).


401
application/json
클라이언트 인증 실패. client_id / client_secret 가 잘못되었거나 클라이언트가 비활성 상태인 경우.

Hide Headers
WWW-AuthenticateCopy link to WWW-Authenticate
Type:string
Basic 인증 챌린지. 토큰 엔드포인트는 Basic realm="openapi" 로 응답합니다.

Type:object · OAuth2ErrorResponse
OAuth2 토큰 발급 실패 응답. /oauth2/token 엔드포인트는 BFF 공통 ErrorResponse envelope 이 아닌 OAuth2 표준 포맷으로 응답합니다. 클라이언트는 code 가 아닌 error 필드로 에러를 식별해야 합니다.

error
Type:string
enum
required
에러 코드.

values
invalid_request
invalid_client
invalid_grant
unauthorized_client
unsupported_grant_type
error_description
Type:string
Example
에러 상세 설명 (선택). 메시지에 non-ASCII 문자가 포함되는 경우 생략될 수 있습니다.

error_uri
Type:string
Format:uri
에러 정보가 게시된 페이지 URI (선택).


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
Request Example forpost/oauth2/token
Shell Curl
curl https://openapi.tossinvest.com/oauth2/token \
  --request POST \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'client_id=c_01HXYZABCDEFG123456789' \
  --data-urlencode 'client_secret=s_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

Status:200
Status:400
Status:401
Status:429

{
  "access_token": "eyJraWQiOiIyMDI2LTA0LTAxLWtleSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJjXzAxSFhZWiJ9...",
  "token_type": "Bearer",
  "expires_in": 86400
}

토큰 발급 성공