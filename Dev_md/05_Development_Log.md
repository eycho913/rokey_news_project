# 5. 개발 로그 (v2.0)

이 문서는 "뉴스 요약·감성분석 웹 앱"의 주요 개발 단계를 기록합니다. 이 로그는 React/FastAPI 아키텍처(v2.0) 기준으로 재작성되었습니다.

## 단계 1: 프로젝트 아키텍처 전환 및 재설정 (완료)
- **작업**: 초기 프로토타입(Streamlit)에서 확장성과 프론트엔드-백엔드 분리를 위해 React/FastAPI 아키텍처로 전환.
- **산출물**:
    - `frontend/`: React + Vite 프로젝트 초기화.
    - `backend-api/`: FastAPI 프로젝트 초기화.
    - `docker-compose.yml`: 프론트엔드(Nginx)와 백엔드(Uvicorn) 컨테이너 구성을 위한 Docker Compose 파일 작성.
    - `.gitignore`: Node.js 및 Python 프로젝트에 맞는 무시 파일 목록 통합.

## 단계 2: 백엔드 핵심 기능 구현 (완료)
- **작업**: 뉴스 분석을 위한 핵심 백엔드 서비스 및 API 엔드포인트를 구현.
- **산출물**:
    - `services/news_client.py`: URL로부터 웹 페이지를 스크래핑하는 기능 구현.
    - `services/text_extract.py`: 스크래핑된 HTML에서 본문을 추출하고 정제하는 기능 구현.
    - `services/summarizer.py` & `services/sentiment.py`: Gemini API를 사용하여 텍스트를 요약하고 감성을 분석하는 초기 서비스 구현.
    - `main.py`: `/analyze` 엔드포인트를 생성하여 서비스들을 오케스트레이션하고, `AnalyzeRequest` 및 `AnalyzeResponse` Pydantic 모델을 정의.

## 단계 3: 프론트엔드 UI 구현 (완료)
- **작업**: 사용자가 뉴스 URL과 API 키를 입력하여 분석을 요청하고 결과를 확인할 수 있는 기본 UI를 React로 구현.
- **산출물**:
    - `frontend/src/App.tsx`: 뉴스 URL, API 키, 요약 길이 등을 입력받는 폼(Form) UI 구현.
    - "분석 실행" 버튼 클릭 시 백엔드 `/analyze` 엔드포인트를 호출하는 비동기 로직 작성.
    - 로딩 및 오류 상태를 처리하고, 분석 결과를 화면에 렌더링하는 컴포넌트 구조 완성.
    - 감성 점수에 따라 텍스트 색상을 다르게 표시하는 기능 구현.

## 단계 4: LLM 공급자 확장 (완료)
- **작업**: 백엔드에서 Gemini 외에 OpenAI 호환 API도 사용할 수 있도록 아키텍처를 확장.
- **산출물**:
    - `services/openai_summarizer.py` & `services/openai_sentiment.py`: OpenAI API를 사용하여 요약 및 감성 분석을 수행하는 서비스 클래스 추가.
    - `main.py` 리팩토링: 요청에 `llm_provider` 필드를 추가하여 Gemini와 OpenAI 서비스를 동적으로 선택하도록 로직 수정. `AnalyzeRequest` 모델을 새로운 규격에 맞게 업데이트.

## 단계 5: 프론트엔드 LLM 공급자 선택 기능 추가 (완료)
- **작업**: 백엔드 확장 기능에 맞춰 프론트엔드 UI를 업데이트.
- **산출물**:
    - `frontend/src/App.tsx` 수정:
        - LLM 공급자(Gemini/OpenAI)를 선택할 수 있는 드롭다운 메뉴 추가.
        - API 키 입력 필드를 "Gemini API Key"에서 범용적인 "Open API Key"로 변경.
        - OpenAI 선택 시 모델 이름을 입력할 수 있는 추가 필드 구현.
        - 백엔드 API 요청 본문을 새로운 규격(`llm_provider`, `llm_api_key` 등)에 맞게 수정.

## 단계 6: 문서 현행화 (진행 중)
- **작업**: Streamlit 기반의 기존 문서를 현재의 React/FastAPI 아키텍처에 맞게 수정.
- **산출물**:
    - `README.md`: Docker Compose 기반의 새로운 실행 방법을 명시하고, 프로젝트 개요를 현행화. (완료)
    - `Dev_md/01_Development_Documentation.md`: 프로젝트 목표와 아키텍처를 v2.0에 맞게 재작성. (완료)
    - `Dev_md/06_Development_Plan.md`: 향후 개발 계획을 담은 To-Do 리스트 신규 작성. (완료)
    - `Dev_md/05_Development_Log.md`: 개발 로그를 v2.0에 맞게 재작성. (완료)
    - 나머지 문서들(`02`, `03`, `04`)도 순차적으로 업데이트 예정.
