# 뉴스 요약 및 감성 분석 Streamlit 앱

**Rokey News Project**는 사용자가 입력한 키워드를 기반으로 최신 뉴스 기사를 검색하고, 각 기사의 핵심 내용을 요약하며, 감성(긍정/부정/중립)을 분석하여 한 화면에 보여주는 Streamlit 웹 애플리케이션입니다.

## 🚀 주요 기능 (v1.0 MVP)

-   **키워드 기반 뉴스 검색**: 사용자가 원하는 키워드를 입력하여 관련 뉴스 기사를 검색합니다.
-   **뉴스 요약**: 각 기사의 본문을 요약하여 핵심 내용을 빠르게 파악할 수 있도록 합니다.
-   **감성 분석**: 기사의 내용이 긍정적인지, 부정적인지, 중립적인지 감성 점수와 함께 표시합니다.
-   **통합 결과 화면**: 검색된 뉴스 목록, 요약, 감성 분석 결과를 한눈에 볼 수 있도록 제공합니다.
-   **결과 저장/공유**: 분석된 결과를 JSON 또는 CSV 형식으로 저장하거나 클립보드로 복사할 수 있습니다.

## 📊 감성 분석 점수 해석 가이드

감성 분석 결과는 `-1.0` (매우 부정)부터 `1.0` (매우 긍정) 사이의 `스코어(Score)`와 이에 해당하는 `레이블(Label)`로 구성됩니다.

-   **스코어**: 텍스트의 감성 강도를 나타내는 수치입니다.
    -   `1.0`에 가까울수록 매우 긍정적입니다.
    -   `-1.0`에 가까울수록 매우 부정적입니다.
    -   `0`에 가까울수록 중립적입니다.
-   **레이블**: 스코어에 기반하여 분류된 감성 범주입니다.
    -   **Positive (긍정)**: 텍스트가 긍정적인 내용을 담고 있습니다. (기본 임계값: `0.3` 초과)
    -   **Neutral (중립)**: 텍스트가 중립적이거나 긍정/부정의 강도가 약합니다. (기본 임계값: `-0.3` 이상 `0.3` 이하)
    -   **Negative (부정)**: 텍스트가 부정적인 내용을 담고 있습니다. (기본 임계값: `-0.3` 미만)

**주의사항**:
뉴스 기사는 특성상 객관적인 사실 전달을 목적으로 하므로, 감성 분석 결과가 '중립'으로 나올 확률이 높습니다. 또한, AI 모델의 특성상 완벽한 감성 분석은 어려울 수 있으며, 특정 문맥이나 비유적 표현 등에서는 오판이 있을 수 있습니다. 사용자는 Streamlit 앱 사이드바에서 임계값을 직접 조절하여 감성 분류의 기준을 변경할 수 있습니다.


## 🛠️ 기술 스택

-   **프론트엔드/백엔드**: Python, Streamlit
-   **뉴스 데이터**: NewsAPI
-   **요약/감성 분석**: Google Gemini API
-   **웹 스크래핑**: BeautifulSoup4, LXML
-   **환경 변수 관리**: python-dotenv

## 🏁 시작하기

이 프로젝트를 로컬 환경에서 실행하려면 다음 단계를 따르세요.

### 1. 리포지토리 클론

```bash
git clone https://github.com/eycho913/rokey_news_project.git
cd rokey_news_project
```

### 2. 가상 환경 설정 및 의존성 설치

Python 가상 환경을 생성하고 활성화한 후 필요한 라이브러리들을 설치합니다.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고, 필요한 API 키들을 추가합니다. `.env.example` 파일을 참조하세요.

```ini
# .env 파일 내용 예시
NEWS_API_KEY=YOUR_NEWS_API_KEY
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```
`YOUR_NEWS_API_KEY`와 `YOUR_GEMINI_API_KEY`를 실제 발급받은 API 키로 대체해야 합니다.

### 4. 애플리케이션 실행

Streamlit 애플리케이션을 실행합니다.

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` (또는 지정된 포트)로 접속하여 앱을 사용할 수 있습니다.

## 🔒 환경 변수 및 보안

API 키와 같은 민감한 정보는 소스 코드에 직접 노출되지 않도록 관리해야 합니다.

-   **로컬 개발**: 프로젝트 루트의 `.env` 파일을 사용하여 환경 변수를 설정합니다. `python-dotenv` 라이브러리가 이를 자동으로 로드합니다. `.gitignore` 파일에 `.env`가 포함되어 있어 Git 저장소에 커밋되지 않습니다.
-   **CI/CD 환경 (GitHub Actions)**: GitHub Actions와 같은 CI/CD 환경에서는 `.env` 파일을 사용하지 않고 **GitHub Secrets**를 활용하여 민감한 정보를 안전하게 관리합니다. 워크플로우(`ci.yml`)에서 `NEWS_API_KEY`, `GEMINI_API_KEY` 등의 환경 변수를 GitHub Secrets에 설정된 값으로 주입해야 합니다.

## 🚀 배포 가이드

Streamlit 앱은 `Streamlit Cloud`를 통해 쉽게 배포할 수 있습니다.

1.  **GitHub 리포지토리 준비**: `app.py`, `requirements.txt`, `.streamlit/config.toml` (선택 사항) 등 필요한 파일들이 GitHub 리포지토리에 커밋되어 있어야 합니다. `main` 브랜치에 푸시된 최신 코드를 사용합니다.
    *   `app.py`
    *   `requirements.txt`
    *   `.env.example` (보안을 위해 `.env` 파일 자체는 커밋하지 마세요!)
    *   `.gitignore`
    *   `services/` 폴더
    *   `tests/` 폴더

2.  **Streamlit Cloud 접속**: [share.streamlit.io](https://share.streamlit.io/) 에 접속하여 GitHub 계정으로 로그인합니다.

3.  **새 앱 배포**: "New app" 버튼을 클릭합니다.

4.  **리포지토리 정보 입력**:
    *   **Repository**: 배포할 앱의 GitHub 리포지토리(`eycho913/rokey_news_project`)를 선택합니다.
    *   **Branch**: 앱을 배포할 브랜치(예: `main`)를 선택합니다.
    *   **Main file path**: Streamlit 앱의 메인 파일 경로(예: `app.py`)를 입력합니다.

5.  **Secrets 설정**:
    *   `Advanced settings`를 클릭하여 환경 변수(`Secrets`)를 설정합니다. `.env` 파일의 내용을 기반으로 `NEWS_API_KEY`, `GEMINI_API_KEY`를 GitHub Secrets에 저장한 값과 동일하게 추가합니다.
        ```
        NEWS_API_KEY="YOUR_NEWS_API_KEY"
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        ```
    *   (스크린샷 자리표시: Streamlit Cloud Secrets 설정 화면)

6.  **Deploy!**: "Deploy!" 버튼을 클릭하면 앱이 배포되기 시작합니다. 배포는 몇 분 정도 소요될 수 있습니다.

7.  **앱 확인**: 배포가 완료되면 앱의 URL을 통해 접근할 수 있습니다.
    *   (스크린샷 자리표시: 성공적으로 배포된 Streamlit 앱 화면)

## ❓ FAQ (자주 묻는 질문)

### 1. `NewsAPIException: API 요청 할당량을 초과했습니다. (429 Too Many Requests)` 오류가 발생합니다.

*   **원인**: NewsAPI는 무료 요금제 사용 시 1분당 5회, 하루 100회의 요청 제한이 있습니다. 단시간에 너무 많은 요청을 보내거나 하루 할당량을 초과하면 발생합니다.
*   **해결 방법**:
    *   잠시 기다린 후 다시 시도합니다.
    *   NewsAPI 유료 플랜으로 업그레이드를 고려합니다.
    *   `news_client.py`의 `page_size`를 줄여 한 번에 가져오는 기사 수를 제한합니다.

### 2. 특정 기사에서 "요약 실패" 또는 "감성 분석 중 오류 발생" 메시지가 나타납니다.

*   **원인**:
    *   뉴스 기사 본문이 너무 짧거나, 내용을 추출할 수 없는 형식일 수 있습니다.
    *   Gemini API 호출 중 일시적인 네트워크 오류가 발생했을 수 있습니다.
    *   Gemini 모델이 해당 콘텐츠를 안전성 정책에 따라 차단했을 수 있습니다.
*   **해결 방법**:
    *   해당 기사는 건너뛰고 다른 기사를 시도합니다.
    *   프롬프트가 너무 민감한 내용을 포함하고 있지 않은지 확인합니다. (가능성은 낮지만)

### 3. `NewsAPIException: 요청 시간이 초과되었습니다. (Timeout)` 오류가 발생합니다.

*   **원인**: NewsAPI 서버 응답이 지연되거나 네트워크 연결에 문제가 있을 수 있습니다.
*   **해결 방법**:
    *   네트워크 연결 상태를 확인합니다.
    *   잠시 후 다시 시도합니다.

### 4. 앱 실행 시 `NEWS_API_KEY` 또는 `GEMINI_API_KEY` 오류가 발생합니다.

*   **원인**: `.env` 파일이 올바르게 설정되지 않았거나, API 키가 잘못 입력되었을 수 있습니다.
*   **해결 방법**:
    *   프로젝트 루트에 `.env` 파일이 존재하는지 확인합니다.
    *   `.env` 파일에 `NEWS_API_KEY`와 `GEMINI_API_KEY`가 올바른 형식으로 설정되어 있는지 확인합니다. (`YOUR_API_KEY` 대신 실제 키가 입력되어야 합니다.)
    *   Streamlit Cloud 배포 시에는 GitHub Secrets에 키가 올바르게 설정되어 있는지 확인합니다.