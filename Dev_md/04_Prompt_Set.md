# 4. 개발 프롬프트 세트 (v2.0)

이 문서는 "뉴스 요약·감성분석 웹 앱" (React/FastAPI 기반) 개발에 사용된 프롬프트 세트를 현재 아키텍처에 맞게 재구성한 것입니다.

---

### 프롬프트 01: 프로젝트 아키텍처 및 Docker 설정

-   **역할**: 너는 풀스택 웹 개발자이자 DevOps 전문가다.
-   **목표**: React 프론트엔드와 FastAPI 백엔드로 구성된 웹 애플리케이션의 기본 구조를 설정한다. 전체 서비스를 `docker-compose`로 한 번에 실행할 수 있어야 한다.
-   **요구**:
    -   `frontend` 폴더에 React+Vite(TypeScript) 프로젝트를 생성하라.
    -   `backend-api` 폴더에 FastAPI 프로젝트를 생성하라.
    -   루트 폴더에 `docker-compose.yml`을 작성하라.
        -   `frontend` 서비스는 `nginx`를 사용하여 정적 파일을 서빙해야 한다.
        -   `backend-api` 서비스는 `uvicorn`으로 실행되어야 한다.
        -   두 서비스는 `app-network`라는 동일한 Docker 네트워크를 사용해야 한다.
    -   각 서비스에 맞는 `Dockerfile`을 작성하라.

### 프롬프트 02: 백엔드 API 엔드포인트 구현

-   **목표**: 뉴스 분석을 위한 핵심 백엔드 API(`/analyze`)를 구현한다.
-   **요구**:
    -   `main.py`에 `/analyze` POST 엔드포인트를 만들어라.
    -   Pydantic을 사용하여 요청 본문(`AnalyzeRequest`)과 응답(`AnalyzeResponse`)의 데이터 모델을 정의하라.
    -   `AnalyzeRequest`는 `news_url`, `summary_length`, `llm_provider` (Optional), `llm_api_key` (Optional), `llm_model` (Optional), `llm_api_base` (Optional) 등을 포함해야 한다.
    -   CORS 설정을 추가하여 프론트엔드(`localhost:3000` 등)에서의 요청을 허용하라.

### 프롬프트 02-1: 백엔드 뉴스 검색 API 엔드포인트 구현

-   **목표**: 키워드 기반 뉴스 검색을 위한 백엔드 API (`/search`)를 구현한다.
-   **요구**:
    -   `main.py`에 `/search` GET 엔드포인트를 만들어라.
    -   `q` (검색 키워드)와 `page_size`를 쿼리 파라미터로 받도록 하라.
    -   `news_api_key`를 쿼리 파라미터로 선택적으로 받을 수 있도록 하고, 환경 변수에 설정된 키가 우선하도록 폴백 로직을 구현하라.
    -   `services/news_client.py`를 사용하여 NewsAPI로부터 뉴스를 검색하고 결과를 반환하라.

### 프롬프트 03: 백엔드 핵심 로직 구현

-   **목표**: `/analyze` 엔드포인트의 핵심 비즈니스 로직을 `services/` 폴더에 모듈화하여 구현한다.
-   **요구**:
    -   `news_client.py`: `requests`와 `BeautifulSoup`을 사용하여 주어진 URL의 HTML을 가져오는 함수를 구현하라.
    -   `text_extract.py`: 가져온 HTML에서 기사 본문을 추출하고, 불필요한 공백과 태그를 제거하는 함수를 구현하라.
    -   `summarizer.py`: Gemini API를 사용하여 정제된 텍스트를 요약하는 클래스(`GeminiSummarizer`)를 구현하라.
    -   `sentiment.py`: Gemini API를 사용하여 텍스트의 감성을 5점 리커트 척도로 분석하는 클래스(`GeminiSentimentAnalyzer`)를 구현하라.

### 프롬프트 04: 프론트엔드 UI 및 API 연동

-   **목표**: 사용자가 뉴스 URL, LLM 공급자, LLM API 키, NewsAPI 키 등을 입력하여 분석을 요청하고 결과를 볼 수 있는 React UI를 구현한다.
-   **요구**:
    -   `frontend/src/App.tsx`에 뉴스 URL, LLM 공급자 선택 드롭다운, LLM API 키 입력 필드, LLM 모델 입력 필드(OpenAI 선택 시), NewsAPI 키 입력 필드, 요약 길이 선택 드롭다운, "분석 실행" 버튼 등 필요한 모든 UI 요소를 배치하라.
    -   `useState`를 사용하여 사용자 입력, 로딩 상태, 에러 메시지, 분석 결과를 관리하라.
    -   "분석 실행" 버튼을 클릭하면 `fetch`를 사용하여 백엔드의 `/analyze` 엔드포인트를 호출하는 비동기 함수를 작성하라. 이때, LLM 관련 필드(`llm_provider`, `llm_api_key`, `llm_model`, `llm_api_base`)와 `summary_length`를 JSON 본문에 포함하여 전송하라.
    -   백엔드로부터 받은 결과를 화면에 스타일링하여 표시하라. 감성 점수에 따라 다른 색상을 사용하라.

### 프롬프트 05: LLM 공급자 확장 및 API 키 폴백 로직 구현 (백엔드)

-   **목표**: 백엔드가 Gemini 외에 OpenAI 호환 API도 지원하도록 확장하고, LLM API 키 및 설정에 대한 환경 변수 폴백 로직을 구현한다.
-   **요구**:
    -   `AnalyzeRequest` 모델이 `llm_provider`, `llm_api_key`, `llm_model`, `llm_api_base` 등 더 범용적이고 선택적인 필드를 받도록 수정하라. (이미 완료)
    -   `main.py`의 `/analyze` 엔드포인트에서 `llm_provider` 값에 따라 `Gemini...` 또는 `OpenAI...` 서비스 클래스를 동적으로 사용하도록 리팩토링하라.
    -   `llm_api_key`, `llm_provider`, `llm_model`, `llm_api_base` 등의 LLM 관련 설정이 환경 변수에 정의되어 있으면 이를 우선적으로 사용하고, 환경 변수가 없을 경우 `AnalyzeRequest`를 통해 전달된 값을 사용하도록 폴백 로직을 구현하라.
    -   `openai` 라이브러리를 사용하여 요약 및 감성 분석을 수행하는 `OpenAISummarizer`와 `OpenAISentimentAnalyzer` 클래스를 구현하라. (이미 완료)
    -   `requirements.txt`에 `openai`를 추가하라. (이미 완료)

### 프롬프트 06: 프론트엔드 LLM 및 API 키 입력 UI 구현 (완료)

-   **목표**: 백엔드의 LLM 확장 및 API 키 폴백 기능에 맞춰 프론트엔드 UI를 구현한다.
-   **요구**:
    -   `App.tsx`에 LLM 공급자(Gemini/OpenAI)를 선택하는 드롭다운 UI를 추가하라.
    -   API 키 입력 필드 (예: "Open API Key")와 NewsAPI 키 입력 필드를 구현하라.
    -   "OpenAI" 선택 시, 모델 이름을 입력할 수 있는 텍스트 필드를 동적으로 표시하라.
    -   API 요청 시 수정된 백엔드 규격에 맞는 데이터(`llm_provider`, `llm_api_key`, `llm_model`, `llm_api_base`, `news_api_key` 등)를 전송하도록 `fetch` 호출 코드를 수정하라.

### 프롬프트 07: 문서 현행화

-   **목표**: 아키텍처 변경에 따라 모든 주요 문서를 현재 상태에 맞게 업데이트한다.
-   **요구**:
    -   `README.md`를 React/FastAPI 아키텍처 기준으로 재작성하고, `docker-compose` 실행 방법을 포함하라. (완료)
    -   `Dev_md/` 폴더의 모든 문서를 v2.0 아키텍처에 맞게 수정하거나 재작성하라. (완료)
