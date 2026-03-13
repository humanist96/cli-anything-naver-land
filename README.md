# cli-anything-naver-land

네이버 부동산(Naver Land) 매물 정보를 터미널에서 검색하는 CLI 도구입니다.

서울 25개 구의 아파트 매매/전세/월세 매물을 검색하고, 필터링하고, CSV/JSON/Excel로 내보낼 수 있습니다.

## 주요 기능

- **지역 검색** — 구 이름으로 매물 검색 (예: 강남구, 서초구)
- **단지명 검색** — 아파트 단지명으로 검색 (예: 래미안, 힐스테이트)
- **다양한 필터** — 평형, 가격, 층수 등으로 결과 필터링
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

### 기본 검색

```bash
# 강남구 매매 매물 검색
cli-anything-naver-land search region -d 강남구 -t 매매

# 서초구 전세 매물 검색
cli-anything-naver-land search region -d 서초구 -t 전세

# 여러 거래유형 동시 검색
cli-anything-naver-land search region -d 송파구 -t 매매 -t 전세
```

### 단지명 검색

```bash
# 강남구에서 '래미안' 단지 검색
cli-anything-naver-land search complex -n 래미안 -d 강남구
```

### 필터 적용

```bash
# 30평대, 가격 5억~15억
cli-anything-naver-land search region -d 강남구 -t 매매 --type 30평대 --min-price 5억 --max-price 15억

# 전용면적 기준 필터
cli-anything-naver-land search region -d 서초구 -t 전세 --min-area 84 --max-area 120

# 10층 이상만
cli-anything-naver-land search region -d 강남구 -t 매매 --floor 10+
```

### JSON 출력

```bash
cli-anything-naver-land --json search region -d 종로구 -t 매매 -n 5
```

### 내보내기

```bash
# 먼저 검색 후, 결과를 파일로 저장
cli-anything-naver-land search region -d 강남구 -t 매매
cli-anything-naver-land export csv -o 강남구_매매.csv
cli-anything-naver-land export json -o 강남구_매매.json
cli-anything-naver-land export excel -o 강남구_매매.xlsx
```

### 대화형 모드 (REPL)

```bash
# 인자 없이 실행하면 대화형 모드 진입
cli-anything-naver-land
```

REPL 모드에서 사용 가능한 명령어:

| 명령어 | 설명 |
|--------|------|
| `search region -d <구> -t <거래유형>` | 지역 검색 |
| `search complex -n <단지명> -d <구>` | 단지명 검색 |
| `search districts` | 지원 지역 목록 |
| `filter apply --type <평형>` | 필터 적용 |
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

## 지원 지역 (서울 25개 구)

강남구, 강동구, 강북구, 강서구, 관악구, 광진구, 구로구, 금천구, 노원구, 도봉구, 동대문구, 동작구, 마포구, 서대문구, 서초구, 성동구, 성북구, 송파구, 양천구, 영등포구, 용산구, 은평구, 종로구, 중구, 중랑구

## FAQ

### Q: "구" 를 빼고 검색해도 되나요?

네, `강남`으로 검색해도 `강남구`로 인식됩니다.

### Q: Excel 내보내기가 안 돼요

openpyxl 패키지를 설치하세요:

```bash
pip install openpyxl
```

또는 처음부터 Excel 지원 포함 설치:

```bash
pip install -e ".[excel]"
```

### Q: 서울 외 지역도 검색할 수 있나요?

현재 버전은 서울 25개 구만 지원합니다.

### Q: 검색 속도가 느려요

네이버 API 부하 방지를 위해 요청 사이에 딜레이가 있습니다. 정상적인 동작입니다.

## 라이선스

MIT License
