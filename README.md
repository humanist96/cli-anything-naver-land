# cli-anything-naver-land

네이버 부동산(Naver Land) 매물 정보를 터미널에서 검색하는 CLI 도구입니다.

**전국 17개 시/도, 248개 구/군/시**의 아파트 매매/전세/월세 매물을 검색하고, 필터링하고, CSV/JSON/Excel로 내보낼 수 있습니다.

## 주요 기능

- **자연어 검색** — `nlq 강남 30평대 매매 10억 이하` 한 줄로 검색
- **전국 검색** — 서울뿐 아니라 부산, 대구, 경기도 등 전국 17개 시/도 지원
- **지역 모호성 감지** — "중구"처럼 여러 도시에 있는 지역명 자동 감지 및 안내
- **단지명 검색 (고속)** — 검색 리다이렉트로 hscpNo 즉시 조회, 3단계 fallback (~30초)
- **확장 필터** — 평형, 가격, 층수, 날짜, 태그, 단지명, 월세 등
- **매물 URL 생성** — 네이버 부동산 매물 상세/지도 링크 자동 생성
- **요약 통계** — 가격 범위, 평균, 평형 분포 등 검색 결과 분석
- **결과 캐시** — 동일 조건 재검색 시 즉시 반환 (5분 TTL)
- **내보내기** — CSV, JSON, Excel 형식으로 저장
- **대화형 REPL** — 인터랙티브 모드에서 연속 검색
- **세션 관리** — 검색 히스토리, 되돌리기(undo/redo)

## 사전 요구사항

- **Python 3.9** 이상
- pip (Python 패키지 관리자)

## 설치 방법

### 방법 1: 저장소 클론 후 설치 (권장)

```bash
git clone https://github.com/humanist96/cli-anything-naver-land.git
cd cli-anything-naver-land
pip install -e .
```

### 방법 2: 바로 설치

```bash
pip install git+https://github.com/humanist96/cli-anything-naver-land.git
```

### Excel 내보내기가 필요한 경우

```bash
pip install -e ".[excel]"
```

## 사용법

### 자연어 검색 (추천)

가장 쉬운 방법! 한국어로 자연스럽게 검색할 수 있습니다:

```bash
# 강남구 30평대 매매 10억 이하
cli-anything-naver-land nlq 강남 30평대 매매 10억 이하

# 부산 해운대 전세 84㎡ 이상
cli-anything-naver-land nlq 부산 해운대 전세 84㎡ 이상

# 서초구 반포자이 매매 제일 싼거
cli-anything-naver-land nlq 서초구 반포자이 매매 제일 싼거

# 종로구 매물 CSV로 저장
cli-anything-naver-land nlq 종로구 전체 매물 csv로 저장

# 강남구 매매 20층 이상
cli-anything-naver-land nlq 강남구 매매 20층 이상

# 가격 범위 검색
cli-anything-naver-land nlq 강남구 매매 5억~15억
```

자연어 파서가 인식하는 키워드:
- **거래유형**: 매매, 전세, 월세, 단기임대
- **평형**: 소형, 20평대, 30평대, 중대형
- **가격**: `10억 이하`, `5억 이상`, `5억~15억`
- **면적**: `84㎡ 이상`, `30평 이하`
- **층수**: `20층 이상`, `5층 이하`
- **정렬**: 싼, 저렴한, 최신, 넓은
- **내보내기**: csv, json, excel, 저장, 다운로드

### 기본 검색 (서울)

```bash
# 강남구 매매 매물 검색
cli-anything-naver-land search region -d 강남구 -t 매매

# 서초구 전세 매물 검색
cli-anything-naver-land search region -d 서초구 -t 전세

# 여러 거래유형 동시 검색
cli-anything-naver-land search region -d 송파구 -t 매매 -t 전세
```

### 전국 검색 (`-c` 옵션)

```bash
# 부산 해운대구 매매
cli-anything-naver-land search region -c 부산시 -d 해운대구 -t 매매

# 경기도 분당구 전세
cli-anything-naver-land search region -c 경기도 -d 분당구 -t 전세

# 대전 유성구 매매
cli-anything-naver-land search region -c 대전 -d 유성구 -t 매매

# 제주 제주시 매매
cli-anything-naver-land search region -c 제주 -d 제주시 -t 매매
```

> **참고:** 서울은 `-c` 없이도 자동 검색됩니다. 다른 시/도는 `-c`로 지정하세요.

### 단지명 검색 (고속 검색)

검색 리다이렉트를 활용한 3단계 fallback으로 기존 대비 **~5배 빠른** 단지 검색:

```bash
# 단지명만으로 검색 (구 지정 불필요 — 검색 리다이렉트로 즉시 조회)
cli-anything-naver-land search complex -n 목동7단지
cli-anything-naver-land search complex -n 도곡렉슬
cli-anything-naver-land search complex -n 래미안목동아델리체

# 구 지정도 가능 (리다이렉트 실패 시 complexList fallback)
cli-anything-naver-land search complex -n 래미안 -d 강남구

# 부산 해운대구에서 '엘시티' 검색
cli-anything-naver-land search complex -n 엘시티 -d 해운대구 -c 부산시
```

> **속도 비교:** 기존 구 전체 매물 수집 방식(~2분 30초) → 검색 리다이렉트 방식(**~30초**, API 호출 5회 이내)

### 지역 목록 조회

```bash
# 지원 시/도 목록
cli-anything-naver-land search cities

# 특정 시/도의 구/군 목록
cli-anything-naver-land search districts -c 부산시
cli-anything-naver-land search districts -c 경기도

# 서울 구 목록 (기본값)
cli-anything-naver-land search districts
```

### 필터 적용

```bash
# 30평대, 가격 5억~15억
cli-anything-naver-land search region -d 강남구 -t 매매 --type 30평대 --min-price 5억 --max-price 15억

# 전용면적 기준 필터
cli-anything-naver-land search region -c 부산 -d 해운대구 -t 전세 --min-area 84 --max-area 120

# 10층 이상만
cli-anything-naver-land search region -d 강남구 -t 매매 --floor 10+

# 태그 필터 (역세권, 신축 등)
cli-anything-naver-land search region -d 강남구 -t 매매 --tag 역세권 --tag 신축

# 확인일 기간 필터
cli-anything-naver-land search region -d 강남구 -t 매매 --since 2026-03-01

# 단지명 포함 필터
cli-anything-naver-land search region -d 강남구 -t 매매 --name-contains 래미안
```

### 매물 URL 조회

```bash
# 매물번호로 네이버 부동산 URL 생성
cli-anything-naver-land search url -a 2419574826

# 구/군 지도 URL 생성
cli-anything-naver-land search url -d 강남구

# 현재 검색 결과의 URL 보기 (검색 후)
cli-anything-naver-land search url
```

### 지역 모호성 감지

"중구"처럼 여러 도시에 존재하는 지역명을 검색하면 자동으로 안내합니다:

```
$ cli-anything-naver-land search region -d 중구 -t 매매

  ⚠ '중구'이(가) 여러 도시에 있습니다:
    [1] 서울시 중구
    [2] 부산시 중구
    [3] 대구시 중구
    [4] 인천시 중구
    [5] 대전시 중구
    [6] 울산시 중구
  → -c 옵션으로 시/도를 지정하세요 (예: -c 부산)
```

### JSON 출력

```bash
cli-anything-naver-land --json search region -d 종로구 -t 매매 -n 5
```

### 내보내기

```bash
# 먼저 검색 후, 결과를 파일로 저장
cli-anything-naver-land search region -c 부산 -d 해운대구 -t 매매
cli-anything-naver-land export csv -o 해운대_매매.csv
cli-anything-naver-land export json -o 해운대_매매.json
cli-anything-naver-land export excel -o 해운대_매매.xlsx
```

### 대화형 모드 (REPL)

```bash
# 인자 없이 실행하면 대화형 모드 진입
cli-anything-naver-land
```

REPL 모드에서 사용 가능한 명령어:

| 명령어 | 설명 |
|--------|------|
| `nlq <자연어>` | 자연어 검색 (예: `nlq 강남 30평대 매매 10억 이하`) |
| `search region -d <구>` | 서울 지역 검색 |
| `search region -c <시/도> -d <구>` | 전국 지역 검색 |
| `search complex -n <단지명> -d <구>` | 단지명 검색 |
| `search url [-a 매물번호] [-d 구]` | 네이버 매물/지도 URL 생성 |
| `search cities` | 시/도 목록 |
| `search districts [-c <시/도>]` | 구/군 목록 |
| `filter apply` | 필터 적용 (`--type`, `--min-price`, `--tag`, `--since` 등) |
| `filter clear` | 필터 초기화 |
| `filter show` | 현재 필터 보기 |
| `export csv -o <파일>` | CSV 내보내기 |
| `export json -o <파일>` | JSON 내보내기 |
| `export excel -o <파일>` | Excel 내보내기 |
| `session history` | 명령 히스토리 |
| `session undo` | 되돌리기 |
| `session redo` | 다시실행 |
| `help` | 도움말 |
| `quit` | 종료 |

## 검색 옵션 상세

### 시/도 (`-c`)

| 값 | 설명 |
|----|------|
| `서울시` (또는 `서울`) | 서울특별시 — 25개 구 |
| `부산시` (또는 `부산`) | 부산광역시 — 16개 구/군 |
| `대구시` (또는 `대구`) | 대구광역시 — 9개 구/군 |
| `인천시` (또는 `인천`) | 인천광역시 — 10개 구/군 |
| `광주시` (또는 `광주`) | 광주광역시 — 5개 구 |
| `대전시` (또는 `대전`) | 대전광역시 — 5개 구 |
| `울산시` (또는 `울산`) | 울산광역시 — 5개 구/군 |
| `세종시` | 세종특별자치시 |
| `경기도` (또는 `경기`) | 경기도 — 42개 시/구 |
| `강원도` (또는 `강원`) | 강원특별자치도 — 18개 시/군 |
| `충청북도` (또는 `충북`) | 충청북도 — 14개 시/군 |
| `충청남도` (또는 `충남`) | 충청남도 — 16개 시/군 |
| `전라북도` (또는 `전북`) | 전북특별자치도 — 15개 시/군 |
| `전라남도` (또는 `전남`) | 전라남도 — 22개 시/군 |
| `경상북도` (또는 `경북`) | 경상북도 — 23개 시/군 |
| `경상남도` (또는 `경남`) | 경상남도 — 22개 시/군 |
| `제주도` (또는 `제주`) | 제주특별자치도 — 2개 시 |

### 거래유형 (`-t`)

| 값 | 설명 |
|----|------|
| `매매` | 매매 (분양권 포함) |
| `전세` | 전세 |
| `월세` | 월세 |
| `단기임대` | 단기임대 |

### 부동산유형 (`-p`)

| 값 | 설명 |
|----|------|
| `APT` | 아파트 (기본값) |
| `VL` | 빌라/연립 |
| `OPST` | 오피스텔 |
| `OR` | 주거용오피스텔 |
| `ABYG` | 아파트분양권 |
| `JGC` | 재건축 |
| `DDDGG` | 단독/다가구 |

### 평형 분류 (`--type`)

| 값 | 설명 |
|----|------|
| `소형` | ~59㎡ (약 18평 이하) |
| `20평대` | 59~85㎡ |
| `30평대` | 85~135㎡ |
| `중대형` | 135㎡~ |

### 정렬 (`--sort`)

| 값 | 설명 |
|----|------|
| `rank` | 추천순 (기본값) |
| `prc` | 가격순 |
| `spc` | 면적순 |
| `date` | 최신순 |

### 층 필터 (`--floor`)

| 형식 | 의미 |
|------|------|
| `10+` | 10층 이상 |
| `3-10` | 3~10층 |
| `5` | 5층만 |

### 가격 필터 (`--min-price`, `--max-price`)

| 형식 | 의미 |
|------|------|
| `5억` | 5억원 |
| `8억 5,000` | 8억 5천만원 |
| `50000` | 5억원 (만원 단위) |

### 확장 필터 (v1.1)

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--since` | 확인일 시작 | `--since 2026-03-01` |
| `--until` | 확인일 끝 | `--until 2026-03-31` |
| `--tag` | 태그 필터 (복수 가능) | `--tag 역세권 --tag 신축` |
| `--name-contains` | 단지명 포함 | `--name-contains 래미안` |

## 검색 결과 요약

검색 결과에 자동으로 요약 통계가 표시됩니다:

```
  종로구 검색 결과
  ──────────────────────────────
  총 매물:    576건
  가격 범위:  2억 3,000 ~ 85억
  평균 가격:  15억 4,200
  평형 분포:  소형 89건 | 20평대 201건 | 30평대 178건 | 중대형 108건
  거래유형:  매매 576건
```

## FAQ

### Q: "구" 를 빼고 검색해도 되나요?

네, `강남`으로 검색해도 `강남구`로 인식됩니다. `해운대`→`해운대구`, `분당`→`성남시 분당구`도 됩니다.

### Q: 서울은 `-c` 없이도 되나요?

네, 서울 지역은 `-c` 옵션 없이 구 이름만으로 검색됩니다. 다른 시/도는 `-c`로 지정하세요.

### Q: Excel 내보내기가 안 돼요

openpyxl 패키지를 설치하세요:

```bash
pip install openpyxl
```

또는 처음부터 Excel 지원 포함 설치:

```bash
pip install -e ".[excel]"
```

### Q: 같은 검색을 다시 하면 빨라요?

네, 동일 조건의 검색 결과는 5분간 캐시됩니다. 캐시된 결과는 API 호출 없이 즉시 반환됩니다.

### Q: 검색 속도가 느려요

네이버 API 부하 방지를 위해 요청 사이에 딜레이가 있습니다. 정상적인 동작입니다. REPL 모드에서는 세션이 재사용되어 초기 연결 시간이 절약됩니다.

**단지명 검색**은 검색 리다이렉트를 활용해 기존 대비 ~5배 빠릅니다. `search complex -n 단지명`을 사용하세요.

### Q: "중구"를 검색하면 어떤 도시의 중구인가요?

`-c` 옵션 없이 검색하면 여러 도시에 있는 지역명을 자동 감지하여 선택을 요청합니다. `-c 부산`처럼 시/도를 지정하면 해당 도시의 중구를 검색합니다.

## 라이선스

MIT License
