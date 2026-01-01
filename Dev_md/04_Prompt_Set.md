# 4. 개발 프롬프트 세트

이 문서는 "뉴스 요약·감성분석 Streamlit 앱" 개발에 사용된 8단계 프롬프트 세트를 기록합니다.

---

### 프롬프트 01: 프로젝트 부트스트랩

-   **역할**: 너는 시니어 파이썬 엔지니어이자 MLOps 실무자다.
-   **목표**: “뉴스 요약+감성분석 Streamlit 앱”의 최소 실행 뼈대를 만든다.
-   **요구**:
    -   폴더 구조 생성 (`services/`, `data/`, `tests/`).
    -   `requirements.txt`, `.env.example`, `.gitignore` 작성.
    -   `app.py`는 “키워드 입력 → 검색 버튼 → 더미 결과 표시”까지 동작하게 하라.
    -   실행 방법을 `README.md`에 적어라.
-   **제약**: API 키는 코드에 하드코딩 금지. `python-dotenv`로 로드.

### 프롬프트 02: NewsAPI 연동 + JSON 저장

-   **목표**: `services/news_client.py`를 구현해 NewsAPI 호출로 기사 목록을 가져오고, `data/` 폴더에 JSON으로 저장하라.
-   **요구**:
    -   입력: `keyword`, `from_date`, `to_date`, `language`, `page_size`
    -   출력: `NewsItem` 리스트
    -   예외: 429(쿼터), 타임아웃, 빈 결과 처리
    -   Streamlit UI에 “기사 수/저장 경로” 표시
    -   테스트: `tests/test_news_client.py`에 최소 2개 케이스 작성(모킹 사용)

### 프롬프트 03: 본문 정제

-   **목표**: `services/text_extract.py` 구현
-   **요구**:
    -   `content_raw`에서 HTML/불필요 공백 제거
    -   너무 긴 텍스트는 토큰/문자 기준으로 자르기
    -   “본문이 없는 기사”는 대체 텍스트 생성(제목+설명+출처)
    -   결과: 요약 입력으로 쓸 `content_clean` 반환

### 프롬프트 04: 제미나이로 요약 구현

-   **목표**: `services/summarizer.py`에서 Gemini API로 요약 생성
-   **요구**:
    -   요약 길이 옵션(short/medium/long)
    -   출력 형식: 3~7개 불릿 + 한 줄 결론
    -   방어: 기사 본문 내 지시문 무시(프롬프트 인젝션 방어 문구 포함)
    -   실패 시 graceful fallback(요약 실패 메시지 + 원문 링크)
    -   추가: 호출 비용/속도 고려해 캐시 적용

### 프롬프트 05: 감성 분석 구현

-   **목표**: `services/sentiment.py` 구현 (Gemini 또는 간단 모델)
-   **요구**:
    -   출력: `label(positive/neutral/negative)`, `score`
    -   점수 정의를 `README.md`에 명시
    -   기사 특성상 중립 많음을 고려해 임계값(threshold) 옵션 제공
    -   실패 시 `neutral` 처리 + 경고 메시지

### 프롬프트 06: UI 통합

-   **목표**: `app.py`에 전체 플로우 통합
-   **요구**:
    -   진행률(progress bar)
    -   기사 리스트 + 상세 보기(선택 시 요약/감성 표시)
    -   JSON/CSV 다운로드 버튼
    -   예외/경고 UI(본문없음, 요약실패 등)

### 프롬프트 07: 통합 테스트 + 린트 + CI

-   **목표**: GitHub Actions로 CI 구성
-   **요구**:
    -   `pytest` 실행
    -   `ruff` 또는 `flake8` 린트
    -   PR 시 자동 실행
    -   배포 키/시크릿 노출 방지 체크리스트 추가

### 프롬프트 08: 배포 가이드 문서

-   **목표**: `README.md`를 “실행/환경변수/배포(Render 또는 Streamlit Cloud)/FAQ”까지 완성
-   **요구**:
    -   로컬 실행 명령
    -   환경변수 목록
    -   배포 단계별 스크린샷 자리표시
    -   흔한 오류(429, 본문없음, 타임아웃) 대응법
