# 5. 개발 로그

이 문서는 "뉴스 요약·감성분석 Streamlit 앱"의 주요 개발 단계를 기록합니다.

## 단계 1: 프로젝트 부트스트랩 (완료)
- **작업**: Python/Streamlit 기반의 새로운 프로젝트 구조를 설정하고, 기존 React 관련 파일들을 삭제하여 환경을 정리함.
- **산출물**:
    - `services/`, `data/`, `tests/` 폴더 구조 생성
    - `requirements.txt`: Streamlit, python-dotenv, requests, pytest 등 기본 의존성 추가
    - `.gitignore`: Python 프로젝트에 맞는 무시 파일 목록 업데이트
    - `.env.example`: 필요한 환경 변수(API 키) 명시
    - `app.py`: "키워드 입력 → 검색 버튼 → 더미 결과"가 표시되는 기본 UI 뼈대 구현
    - `README.md`: 프로젝트 개요 및 로컬 실행 방법 초기화

## 단계 2: NewsAPI 연동 (완료)
- **작업**: `services/news_client.py`를 구현하여 NewsAPI를 통해 키워드로 뉴스를 검색하고, 결과를 JSON 파일로 저장하는 기능을 개발함.
- **산출물**:
    - `NewsItem` 데이터 클래스 정의
    - `NewsClient` 클래스 구현 (API 호출, 예외 처리 포함)
    - `save_to_json` 함수 구현
    - `tests/test_news_client.py`: NewsAPI 호출 성공, 실패(429, Timeout), 빈 결과 케이스에 대한 단위 테스트 작성
    - `app.py`에 연동하여 실제 API 호출 및 결과 저장/표시 기능 확인

## 단계 3: 본문 정제 기능 구현 (완료)
- **작업**: `services/text_extract.py`를 구현하여 뉴스 기사 본문에서 HTML 태그와 불필요한 공백을 제거하고, 최대 길이를 제한하는 텍스트 정제 기능을 개발함. 본문이 없는 경우 대체 텍스트를 생성하는 로직도 포함.
- **산출물**:
    - `extract_and_clean` 함수 및 헬퍼 함수 구현
    - `tests/test_text_extract.py`: HTML 제거, 공백 정제, 텍스트 자르기, 대체 텍스트 생성 등 다양한 케이스에 대한 단위 테스트 작성
    - `app.py`에 연동하여 정제된 본문을 생성하고 화면에 표시

## 단계 4: Gemini 요약 기능 구현 (완료)
- **작업**: `services/summarizer.py`를 구현하여 Google Gemini API로 텍스트 요약을 생성하는 기능을 개발함. 프롬프트 인젝션 방어, 캐싱, 길이 옵션, 실패 시 폴백 로직을 포함.
- **산출물**:
    - `GeminiSummarizer` 클래스 구현
    - `tests/test_summarizer.py`: 요약 성공, API 오류, 안전성 차단, 캐싱 기능에 대한 단위 테스트 작성
    - `app.py`에 연동하여 각 기사의 요약을 생성하고 UI에 표시

## 단계 5: Gemini 감성 분석 기능 구현 (완료)
- **작업**: `services/sentiment.py`를 구현하여 Gemini API로 텍스트의 감성(긍정/부정/중립)과 점수를 분석하는 기능을 개발함. 사용자 정의 임계값, 캐싱, 실패 시 폴백 로직을 포함.
- **산출물**:
    - `SentimentResult` 데이터 클래스 및 `GeminiSentimentAnalyzer` 클래스 구현
    - `tests/test_sentiment.py`: 긍정/부정/중립 분석, API 오류, 캐싱, 임계값 적용 등 단위 테스트 작성
    - `app.py`에 연동하여 각 기사의 감성을 분석하고 UI에 색상과 함께 표시
    - `README.md`에 감성 점수 해석 가이드 추가

## 단계 6: UI 통합 및 고도화 (완료)
- **작업**: `app.py`의 전체 UI/UX를 개선. 진행률 표시, 기사 선택 기능, 다운로드 기능 등을 추가하여 사용자 경험을 향상시킴.
- **산출물**:
    - `st.progress`를 이용한 실시간 진행률 표시 기능 구현
    - `st.selectbox`와 `st.session_state`를 이용한 기사 선택 및 상세 보기 기능 구현
    - `st.download_button`을 이용한 JSON 및 CSV 다운로드 기능 구현
    - 전반적인 UI 레이아웃 및 사용자 안내 문구 개선

## 단계 7: CI/CD 및 품질 관리 (완료)
- **작업**: GitHub Actions를 사용하여 CI(Continuous Integration) 파이프라인을 구성하고, 코드 품질 관리를 자동화함.
- **산출물**:
    - `ruff` 라이브러리를 `requirements.txt`에 추가
    - `.github/workflows/ci.yml`: Pull Request 및 `main` 브랜치 push 시 `ruff` 린팅과 `pytest` 테스트를 자동으로 실행하는 워크플로우 생성
    - `tests/test_app.py`: 주요 앱 흐름에 대한 통합 테스트(모의) 추가
    - `README.md`에 API 키 보안 관리(GitHub Secrets) 관련 내용 추가

## 단계 8: 최종 문서화 (완료)
- **작업**: `README.md`에 배포 가이드와 FAQ를 추가하여 프로젝트 문서를 최종 완성함.
- **산출물**:
    - `README.md`에 Streamlit Cloud 배포 가이드 섹션 추가
    - `README.md`에 흔한 오류와 해결 방법을 담은 FAQ 섹션 추가
