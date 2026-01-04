# 1. Rokey News Project 개발 문서 (v2.0)

이 문서는 "뉴스 요약 및 감성 분석 웹 앱"의 개발 방향과 현재 아키텍처(v2.0)를 설명합니다. 이 버전은 초기 Streamlit 기반 프로토타입에서 확장된 React/FastAPI 기반의 웹 애플리케이션입니다.

## 1.1. 프로젝트 목표 (v2.1 - UI Key Input)

-   사용자가 뉴스 기사 URL, NewsAPI 키, 그리고 LLM(Large Language Model) API 키를 UI에 직접 입력하여, 해당 기사의 본문을 자동으로 추출하고 LLM을 통해 핵심 내용을 요약하며, 리커트 척도 기반의 감성 분석 결과를 제공하는 웹 애플리케이션을 개발합니다.
-   사용자가 Gemini, OpenAI 등 다양한 LLM 공급자를 직접 선택하고 자신의 API 키를 사용하여 분석을 수행할 수 있는 유연한 환경을 제공합니다.
    *   **API 키 처리**: 보안을 위해 백엔드 환경 변수(`NEWS_API_KEY`, `LLM_API_KEY` 등)가 설정된 경우 이를 우선적으로 사용합니다. 환경 변수가 설정되지 않은 경우에만 UI를 통해 입력된 키를 사용하도록 폴백(fallback) 로직을 적용합니다. 이 방식을 통해 보안 배포와 유연한 테스트/데모 시나리오를 모두 지원합니다.
-   향후 키워드 기반 뉴스 검색, 분석 결과 저장 및 공유 등 확장 기능을 염두에 둔 확장 가능한 아키텍처를 구축합니다.

## 1.2. 기술 스택

-   **프론트엔드**:
    -   **언어/프레임워크**: TypeScript, React
    -   **빌드 도구**: Vite
    -   **UI**: 기본 HTML/CSS (향후 UI 라이브러리 도입 고려)

-   **백엔드**:
    -   **언어/프레임워크**: Python, FastAPI
    -   **핵심 라이브러리**:
        -   `requests`: 외부 API 연동 및 웹 스크래핑
        -   `google-generativeai`: Gemini API 연동
        -   `openai`: OpenAI 호환 API 연동
        -   `beautifulsoup4`, `lxml`: 기사 본문 스크래핑 및 정제
        -   `pydantic`: 데이터 유효성 검사
        -   `uvicorn`: ASGI 서버

-   **인프라 및 배포**:
    -   **컨테이너화**: Docker, Docker Compose
    -   **CI/CD**: GitHub Actions

## 1.3. 프로젝트 구조

-   `frontend/`: React 프론트엔드 애플리케이션
    -   `src/App.tsx`: 메인 UI 컴포넌트 및 비즈니스 로직
    -   `package.json`: 프론트엔드 의존성 관리
    -   `Dockerfile`: 프론트엔드 Nginx 배포용 Docker 이미지 빌드
-   `backend-api/`: FastAPI 백엔드 애플리케이션
    -   `main.py`: API 엔드포인트 정의
    -   `services/`: 핵심 비즈니스 로직 분리
        -   `news_client.py`: 뉴스 데이터 스크래핑
        -   `text_extract.py`: 텍스트 정제
        -   `summarizer.py`: Gemini 기반 요약
        -   `sentiment.py`: Gemini 기반 감성 분석
        -   `openai_summarizer.py`: OpenAI 기반 요약
        -   `openai_sentiment.py`: OpenAI 기반 감성 분석
    -   `requirements.txt`: 백엔드 의존성 관리
    -   `Dockerfile`: 백엔드 Docker 이미지 빌드
-   `docker-compose.yml`: 프론트엔드 및 백엔드 서비스를 함께 오케스트레이션
-   `.github/workflows/ci.yml`: GitHub Actions CI 구성

## 1.4. 개발 문서 링크

-   [02_Rules_and_Guidelines.md](./02_Rules_and_Guidelines.md): 개발 규칙, 가이드라인 및 리스크 관리 방안
-   [03_Content_Evaluation.md](./03_Content_Evaluation.md): 프로젝트 성공 기준 및 평가 항목
-   [04_Prompt_Set.md](./04_Prompt_Set.md): 개발에 사용된 프롬프트 세트
-   [05_Development_Log.md](./05_Development_Log.md): 주요 개발 단계별 로그
-   [06_Development_Plan.md](./06_Development_Plan.md): 다음 개발 계획 (To-Do 리스트)
-   [README.md](../README.md): 프로젝트 실행, 배포, FAQ 가이드