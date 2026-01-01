# 1. Rokey News Project 개발 문서 (v1.0)

이 문서는 "뉴스 요약 및 감성 분석 Streamlit 앱"의 개발 방향과 최종 구조를 설명합니다.

## 1.1. 최종 프로젝트 목표 (v1.0)

-   사용자가 관심 키워드를 입력하면, 관련 최신 뉴스를 API로 가져와 핵심 내용 요약과 긍정/부정 감성 분석 결과를 한 화면에서 보여주는 Python/Streamlit 기반 웹 애플리케이션을 개발합니다.
-   분석 결과는 사용자가 업무 보고, 학습, 시장 동향 파악 등에 활용할 수 있도록 저장 및 공유 기능을 제공합니다.

## 1.2. 최종 기술 스택

-   **언어/프레임워크**: Python, Streamlit
-   **핵심 라이브러리**:
    -   `requests`: NewsAPI 연동
    -   `google-generativeai`: Gemini API 연동 (요약, 감성 분석)
    -   `beautifulsoup4`, `lxml`: 기사 본문 스크래핑 및 정제
    -   `pandas`: 데이터 처리 및 CSV 변환
    -   `python-dotenv`: 환경 변수 관리
    -   `pytest`, `ruff`: 테스트 및 코드 린팅

## 1.3. 프로젝트 구조

-   `app.py`: Streamlit 메인 애플리케이션
-   `services/`: 핵심 비즈니스 로직 분리
    -   `news_client.py`: NewsAPI 연동 및 데이터 관리
    -   `text_extract.py`: 기사 본문 추출 및 정제
    -   `summarizer.py`: Gemini 요약 기능
    -   `sentiment.py`: Gemini 감성 분석 기능
-   `tests/`: 단위 및 통합 테스트
-   `data/`: 생성된 JSON 파일 저장
-   `.github/workflows/ci.yml`: GitHub Actions CI 구성

## 1.4. 개발 문서 링크

-   [02_Rules_and_Guidelines.md](./02_Rules_and_Guidelines.md): 개발 규칙, 가이드라인 및 리스크 관리 방안
-   [03_Content_Evaluation.md](./03_Content_Evaluation.md): 프로젝트 성공 기준 및 평가 항목
-   [04_Prompt_Set.md](./04_Prompt_Set.md): 개발에 사용된 프롬프트 세트
-   [05_Development_Log.md](./05_Development_Log.md): 주요 개발 단계별 로그
-   [README.md](../README.md): 프로젝트 실행, 배포, FAQ 가이드