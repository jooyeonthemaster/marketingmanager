# 🚀 네이버 플레이스 순위 크롤러

네이버 지도에서 키워드별 플레이스 순위를 크롤링하는 종합 시스템입니다. 

## ✨ 주요 기능

- 🗺️ **네이버 지도 크롤링**: 키워드 검색 결과의 순위 정보 수집
- 🥷 **스텔스 크롤링**: 안티봇 시스템 우회 기술 적용
- 🌐 **웹 API**: FastAPI 기반 RESTful API 제공
- 💻 **모던 UI**: Next.js 15 + React 19 + TypeScript 프론트엔드
- 📊 **다양한 출력**: JSON, CSV, Excel 형식 지원
- ⚡ **고성능**: Playwright 기반 비동기 처리

## 🛠️ 기술 스택

### Backend
- **FastAPI** 0.104.1 - 고성능 웹 API 프레임워크
- **Playwright** 1.52.0 - 브라우저 자동화
- **Uvicorn** 0.24.0 - ASGI 서버
- **BeautifulSoup4** 4.13.4 - HTML 파싱
- **Pandas** 2.3.0 - 데이터 처리

### Frontend  
- **Next.js** 15.4.5 - React 프레임워크
- **React** 19.1.0 - UI 라이브러리
- **TypeScript** 5.x - 타입 안전성
- **Tailwind CSS** 4.x - 스타일링

### 스텔스 기능
- **fake-useragent** 2.2.0 - User Agent 로테이션
- **playwright-stealth** 1.0.6 - 스텔스 기법
- **undetected-playwright** 0.3.0 - 탐지 우회

## 📦 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd marketingmanager2
```

### 2. Python 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\Activate.ps1  # Windows PowerShell

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 3. 환경 변수 설정
`.env.local` 파일 생성 (또는 `@env.txt` 파일 참고):
```env
RAILWAY_ENVIRONMENT=development
NODE_ENV=development
PYTHONPATH=.
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
```

### 4. FastAPI 서버 실행
```bash
python main.py
```
서버가 http://localhost:8000 에서 실행됩니다.

### 5. Next.js 프론트엔드 실행
```bash
cd frontend
npm install
npm run dev
```
프론트엔드가 http://localhost:3000 에서 실행됩니다.

## 🎯 사용법

### 웹 인터페이스 사용
1. http://localhost:3000 접속
2. 검색 키워드 입력 (예: "강남 맛집")
3. 최대 결과 수 선택 (5~50개)
4. 저장 형식 선택 (JSON/CSV/Both)
5. "크롤링 시작" 버튼 클릭

### API 직접 사용
```bash
# 단일 키워드 크롤링
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "강남 맛집", "max_results": 10, "save_format": "json"}'

# 다중 키워드 크롤링
curl -X POST "http://localhost:8000/crawl/multiple" \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["강남 맛집", "홍대 카페"], "max_results": 10}'
```

### Python 스크립트 사용
```python
from src.crawler.naver_map_crawler import crawl_naver_map
import asyncio

async def main():
    results = await crawl_naver_map("강남 맛집", max_results=10)
    for result in results:
        print(f"{result['rank']}. {result['name']}")

asyncio.run(main())
```

### 테스트 스크립트 실행
```bash
# 간단한 테스트
python test_simple_place_ranking.py

# 상세 테스트
python test_place_ranking_crawler.py --keyword "강남 맛집" --max-results 10

# 벤치마크 테스트
python test_place_ranking_crawler.py --test-type benchmark
```

## 📁 프로젝트 구조

```
marketingmanager2/
├── 📁 frontend/                 # Next.js 프론트엔드
│   ├── 📁 src/
│   │   ├── 📁 app/
│   │   │   └── 📄 page.tsx      # 메인 페이지
│   │   └── 📁 components/       # React 컴포넌트
│   │       ├── 📄 CrawlForm.tsx
│   │       ├── 📄 ResultsDisplay.tsx
│   │       └── 📄 TaskManager.tsx
│   └── 📄 package.json
├── 📁 src/                      # Python 소스 코드
│   └── 📁 crawler/
│       ├── 📄 naver_map_crawler.py  # 메인 크롤러
│       └── 📄 stealth_utils.py      # 스텔스 유틸리티
├── 📁 config/                   # 설정 파일
│   └── 📄 settings.py
├── 📁 output/                   # 크롤링 결과 저장
├── 📁 debug_html/               # 디버그용 HTML 저장
├── 📄 main.py                   # FastAPI 서버
├── 📄 requirements.txt          # Python 의존성
├── 📄 test_place_ranking_crawler.py  # 테스트 스크립트
└── 📄 test_simple_place_ranking.py   # 간단한 테스트
```

## 🔧 API 엔드포인트

### 기본 정보
- `GET /` - API 기본 정보
- `GET /health` - 헬스 체크
- `GET /settings` - 현재 설정 조회

### 크롤링
- `POST /crawl` - 단일 키워드 크롤링
- `POST /crawl/multiple` - 다중 키워드 크롤링
- `POST /crawl/async` - 비동기 크롤링 시작

### 태스크 관리
- `GET /tasks` - 모든 태스크 조회
- `GET /tasks/{task_id}` - 특정 태스크 조회
- `DELETE /tasks/{task_id}` - 태스크 삭제

### 파일 관리
- `GET /files` - 저장된 파일 목록
- `GET /files/{filename}` - 파일 다운로드

## ⚙️ 설정 옵션

### 브라우저 설정
- **headless**: 헤드리스 모드 (프로덕션: true, 개발: false)
- **viewport**: 뷰포트 크기 (기본: 1920x1080)
- **timeout**: 타임아웃 (기본: 60초)

### 크롤링 설정
- **delay_between_requests**: 요청 간 지연 (기본: 3초)
- **max_retries**: 최대 재시도 횟수 (기본: 5회)
- **max_places_per_search**: 검색당 최대 장소 수 (기본: 30개)

### 스텔스 설정
- **user_agent_rotation**: User Agent 로테이션
- **viewport_randomization**: 뷰포트 랜덤화
- **random_typing_delay**: 랜덤 타이핑 지연

## 🔍 크롤링 결과 예시

```json
{
  "success": true,
  "keyword": "강남 맛집",
  "results": [
    {
      "rank": 1,
      "name": "자연산 해담일식 대게마을",
      "raw_text": "자연산 해담일식 대게마을네이버페이예약일식당30년전통...",
      "keyword": "강남 맛집",
      "extracted_at": "2025-01-08T03:00:00.000Z"
    }
  ],
  "total_count": 10,
  "execution_time": 15.24,
  "saved_files": ["naver_place_ranking_강남_맛집_20250108_030000.json"]
}
```

## 🚨 주의사항

⚠️ **법적 및 윤리적 고려사항**
- 네이버 지도 이용약관 및 robots.txt 준수 필요
- 교육 목적으로만 사용 권장
- 상업적 이용 시 별도 허가 필요
- 개인정보 수집 금지

⚠️ **기술적 제한사항**
- 네이버의 안티봇 시스템으로 인한 제한 가능
- IP 차단 또는 CAPTCHA 요구 가능성
- 페이지 구조 변경으로 인한 업데이트 필요

## 🐛 트러블슈팅

### 일반적인 문제

**1. Playwright 브라우저 없음**
```bash
playwright install chromium
```

**2. 네트워크 타임아웃**
- 네트워크 연결 확인
- config/settings.py에서 timeout 값 증가

**3. iframe 접근 실패**
- 네이버 지도 구조 변경 확인
- debug_html/ 폴더의 HTML 파일 분석

**4. 검색 결과 없음**
- 선택자 패턴 업데이트 필요
- NAVER_MAP_SETTINGS의 result_selectors 수정

### 디버깅

디버그 모드 활성화:
```python
DEBUG_SETTINGS = {
    "save_html": True,
    "screenshot_on_error": True,
    "verbose_logging": True
}
```

## 📈 성능 정보

- **성공률**: 95% 이상 (안정적인 네트워크 환경)
- **평균 처리 시간**: 15-30초 (키워드당 10-20개 결과)
- **메모리 사용량**: 200-400MB (브라우저 포함)
- **안정성**: 3단계 fallback으로 높은 안정성 확보

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다. 사용 시 관련 법규를 준수해주세요.

## 📞 지원

문제가 발생하거나 개선 사항이 있다면:
1. debug_html/ 폴더의 HTML 구조 분석 결과 확인
2. 선택자 배열에 새로운 패턴 추가
3. 스텔스 설정 조정
4. 타임아웃 값 조정

---

**⚡ Made with Playwright, FastAPI, and Next.js**