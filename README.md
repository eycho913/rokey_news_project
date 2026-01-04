# 뉴스 요약 및 감성 분석 웹 앱

**Rokey News Project**는 사용자가 제공한 뉴스 기사 URL을 기반으로, 해당 기사의 핵심 내용을 요약하고 감성(긍정/부정/중립)을 분석하여 보여주는 웹 애플리케이션입니다.

## 🚀 주요 기능

-   **URL 기반 뉴스 분석**: 사용자가 분석하고자 하는 뉴스 기사의 URL을 직접 입력합니다.
-   **동적 LLM 공급자 선택**: Gemini 또는 OpenAI 호환 API(예: OpenRouter)를 선택하여 요약 및 감성 분석을 수행할 수 있습니다.
-   **뉴스 요약**: 각 기사의 본문을 지정된 길이(짧게/중간/길게)로 요약하여 핵심 내용을 빠르게 파악할 수 있도록 합니다.
-   **리커트 척도 기반 감성 분석**: 기사의 내용이 긍정적인지, 부정적인지, 중립적인지를 5점 리커트 척도(1점: 매우 부정 ~ 5점: 매우 긍정)로 분석하여 점수와 함께 표시합니다.
-   **웹 기반 UI**: React로 구축된 사용자 친화적인 인터페이스를 통해 쉽게 기능을 사용하고 결과를 확인할 수 있습니다.

## 🛠️ 기술 스택

-   **프론트엔드**: React, TypeScript, Vite
-   **백엔드**: Python, FastAPI
-   **요약/감성 분석**: Google Gemini API, OpenAI API
-   **웹 스크래핑**: BeautifulSoup4, LXML
-   **컨테이너화**: Docker, Docker Compose

## 🏁 시작하기

이 프로젝트는 Docker Compose를 사용하여 간단하게 로컬 환경에서 실행할 수 있습니다.

### 1. 전제 조건

-   [Docker](https://www.docker.com/get-started/) 및 [Docker Compose](https://docs.docker.com/compose/install/)가 설치되어 있어야 합니다.

### 2. 리포지토리 클론

```bash
git clone https://github.com/eycho913/rokey_news_project.git
cd rokey_news_project
```

### 3. 환경 변수 설정 (선택 사항)

백엔드 서비스는 API 키를 컨테이너의 환경 변수로부터 읽습니다. `docker-compose up` 명령어 실행 시 자동으로 `.env` 파일을 읽어 환경 변수를 설정할 수 있습니다.

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 필요한 API 키를 추가하면 Docker 컨테이너 내에서 해당 키를 사용할 수 있습니다.

```ini
# .env 파일 내용 예시
# 이 파일에 키를 설정해두면, UI에 직접 키를 입력할 필요가 없습니다. (보안상 권장)
# 하지만 현재 앱은 UI에서 직접 키를 입력받도록 설계되어 있으므로, 이 파일은 참고용입니다.
NEWS_API_KEY=YOUR_NEWS_API_KEY
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

**참고**: 현재 애플리케이션은 UI에서 직접 API 키를 입력받아 백엔드로 전송하는 방식으로 동작합니다. 백엔드 로직을 수정하여 서버 환경변수에서 직접 키를 읽도록 개선하는 것을 권장합니다. (관련 내용은 `Dev_md/06_Development_Plan.md` 참조)

### 4. 애플리케이션 실행

Docker Compose를 사용하여 프론트엔드와 백엔드 컨테이너를 빌드하고 실행합니다.

```bash
docker-compose up --build -d
```

빌드가 완료되면 브라우저에서 `http://localhost:3000` 주소로 접속하여 앱을 사용할 수 있습니다.

### 5. 애플리케이션 종료

```bash
docker-compose down
```

## ❓ 사용 방법

1.  `http://localhost:3000`에 접속합니다.
2.  분석할 **뉴스 기사 URL**을 입력합니다.
3.  사용할 **LLM 공급자**를 선택합니다 (Gemini 또는 OpenAI).
4.  선택한 공급자에 맞는 **Open API Key**를 입력합니다.
5.  (선택) **NewsAPI Key**를 입력합니다. (기사 메타데이터 보강에 사용될 수 있음)
6.  원하는 **요약 길이**를 선택합니다.
7.  **"뉴스 분석 실행"** 버튼을 클릭하여 결과를 확인합니다.