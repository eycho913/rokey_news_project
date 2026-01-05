# 5. 개발 로그 (v2.1)

이 문서는 "뉴스 요약·감성분석 웹 앱"의 주요 개발 단계를 기록합니다. 이 로그는 React/FastAPI 아키텍처(v2.1) 기준으로 재작성되었습니다.

## 단계 1: 프로젝트 아키텍처 전환 및 재설정 (완료)
- **작업**: 초기 프로토타입(Streamlit)에서 확장성과 프론트엔드-백엔드 분리를 위해 React/FastAPI 아키텍처로 전환.
- **산출물**:
    - `frontend/`: React + Vite 프로젝트 초기화.
    - `backend_api/`: FastAPI 프로젝트 초기화. (폴더명 변경: `backend-api` -> `backend_api`)
    - `docker-compose.yml`: 프론트엔드(Nginx)와 백엔드(Uvicorn) 컨테이너 구성을 위한 Docker Compose 파일 작성. (백엔드 경로 및 Uvicorn 명령어 수정 포함)
    - `.gitignore`: Node.js 및 Python 프로젝트에 맞는 무시 파일 목록 통합.

## 단계 2: 백엔드 핵심 기능 구현 (완료)
- **작업**: 뉴스 분석을 위한 핵심 백엔드 서비스 및 API 엔드포인트를 구현.
- **산출물**:
    - `services/news_client.py`: URL로부터 웹 페이지를 스크래핑하는 기능 구현.
    - `services/text_extract.py`: 스크래핑된 HTML에서 본문을 추출하고 정제하는 기능 구현.
    - `services/summarizer.py` & `services/sentiment.py`: Gemini API를 사용하여 텍스트를 요약하고 감성을 분석하는 초기 서비스 구현.
    - `main.py`: `/analyze` 엔드포인트를 생성하여 서비스들을 오케스트레이션하고, `AnalyzeRequest` 및 `AnalyzeResponse` Pydantic 모델을 정의.

## 단계 3: 프론트엔드 UI 초기 구현 (완료)
- **작업**: 사용자가 뉴스 URL, LLM 공급자, API 키를 입력하여 분석을 요청하고 결과를 확인할 수 있는 기본 UI를 React로 구현.
- **산출물**:
    - `frontend/src/App.tsx`: 뉴스 URL, LLM 공급자, LLM API 키, NewsAPI 키(선택 사항), 요약 길이 등을 입력받는 폼(Form) UI 구현.
    - "분석 실행" 버튼 클릭 시 백엔드 `/analyze` 엔드포인트를 호출하는 비동기 로직 작성.
    - 로딩 및 오류 상태를 처리하고, 분석 결과를 화면에 렌더링하는 컴포넌트 구조 완성.
    - 감성 점수에 따라 텍스트 색상을 다르게 표시하는 기능 구현.
    - **UI 개선**: Tailwind CSS를 적용하여 UI를 현대적이고 사용자 친화적인 2단 레이아웃으로 개선.

## 단계 4: 키워드 기반 뉴스 검색 기능 추가 (완료)
- **작업**: 키워드를 통한 뉴스 검색 기능을 백엔드와 프론트엔드에 통합.
- **산출물**:
    - `backend_api/main.py`: `NEWS_API_KEY`를 환경 변수에서 로드하는 `/search` GET 엔드포인트 추가.
    - `frontend/src/App.tsx`: 키워드 입력 필드, 검색 버튼, 검색 결과 목록 UI 추가. 검색 결과 클릭 시 해당 URL이 분석 필드에 자동으로 채워지도록 연동.

## 단계 5: API 키 보안 강화 및 LLM 설정 중앙화 (완료)
- **작업**: `LLM_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_BASE`를 백엔드 환경 변수에서 관리하도록 변경하여 보안 강화.
- **산출물**:
    - `backend_api/main.py`: `/analyze` 엔드포인트가 LLM 관련 설정을 환경 변수에서 직접 로드하도록 수정. `AnalyzeRequest` 모델에서 LLM 관련 필드 제거.
    - `frontend/src/App.tsx`: LLM 관련 입력 필드(LLM 공급자, LLM API 키, LLM 모델) 및 NewsAPI 키 입력 필드 UI에서 제거.

## 단계 6: UI를 통한 API 키 입력 재도입 및 폴백 로직 구현 (진행 중)
-   **작업**: 사용자 요청에 따라 `LLM_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_BASE` 및 `NEWS_API_KEY`를 다시 프론트엔드 UI를 통해 입력할 수 있도록 재도입. 백엔드는 환경 변수를 우선하되, 환경 변수 부재 시 UI 입력을 폴백으로 사용하도록 로직 수정.
-   **산출물**:
    - `backend_api/main.py`: `AnalyzeRequest` 모델에 `llm_api_key`, `llm_provider`, `llm_model`, `llm_api_base`를 다시 `Optional` 필드로 추가. `/analyze` 엔드포인트에서 환경 변수를 우선하고, 없는 경우 요청 바디의 키를 사용하도록 수정. `/search` 엔드포인트도 `NewsAPI_key`를 쿼리 파라미터 또는 바디에서 받아 폴백 로직 추가.
    - `frontend/src/App.tsx`: LLM 공급자, LLM API 키, LLM 모델, NewsAPI 키 입력 필드 UI에 재도입. `analyzeNews` 및 `performSearch` 요청 시 해당 키를 전송하도록 수정.

## 단계 7: 문서 현행화 (진행 중)
- **작업**: React/FastAPI 아키텍처 및 최신 개발 내용에 맞춰 `Dev_md` 폴더 내 모든 문서 및 `README.md`를 업데이트.
- **산출물**:
    - `README.md`: Docker Compose 기반의 새로운 실행 방법 명시 및 프로젝트 개요 현행화. (완료)
    - `Dev_md/01_Development_Documentation.md`: 프로젝트 목표와 아키텍처를 v2.1에 맞게 재작성. (완료)
    - `Dev_md/02_Rules_and_Guidelines.md`: API 키 노출 리스크 및 대응 방안 현행화. (완료)
    - `Dev_md/04_Prompt_Set.md`: 개발 프롬프트 세트 현행화. (완료)
    - `Dev_md/03_Content_Evaluation.md`: 프로젝트 성공 기준 현행화. (완료)
    - `Dev_md/05_Development_Log.md`: 개발 로그를 v2.1에 맞게 재작성. (완료)
    - `Dev_md/06_Development_Plan.md`: 향후 개발 계획을 담은 To-Do 리스트 신규 작성 및 현행화. (완료)

## 단계 8: 추가 기능 및 개선 구현 (완료)
- **작업**: 고급 검색 필터, UI/UX 개선, API 성능 최적화, 캐싱, 로깅 및 모니터링 시스템 구축을 진행.
- **산출물**:
    - **고급 뉴스 검색 기능**: `NewsClient` (`backend_api/services/news_client.py`) 및 `/search` 엔드포인트 (`backend_api/main.py`)에 `domains`, `excludeDomains`, `qInTitle` 필터 및 관련 프론트엔드 UI (`frontend/src/components/NewsSearchForm.tsx`) 추가. (완료)
    - **UI/UX 개선**: 뉴스 검색 폼 날짜 입력에 `react-datepicker` 적용, 뉴스 검색 폼 로딩 스피너 구현, 뉴스 검색 결과 표시 개선 (설명 및 스타일링), 입력 필드 상태(에러, 비활성화 등) 시각적 피드백 강화. (`frontend/src/components/NewsSearchForm.tsx`) (완료)
    - **API 성능 최적화**: 외부 API 호출 및 내부 처리 단계에 대한 성능 로깅 추가 (`backend_api/main.py`, `backend_api/services/news_client.py`), 뉴스 URL 스크래핑 결과에 대한 캐싱 추가 (`backend_api/services/news_client.py`). (완료)
    - **캐싱 메커니즘 도입**: FastAPI `/search` 엔드포인트에 응답 캐싱 적용 (`backend_api/main.py`). (완료)
    - **상세 로깅 및 모니터링 시스템 구축**: FastAPI 요청 처리 시간 로깅 미들웨어 구현 (`backend_api/main.py`). (완료)
