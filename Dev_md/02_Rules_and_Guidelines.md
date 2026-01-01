# 2. 개발 규칙 및 가이드라인

## 2.1. 코드 컨벤션
- **언어**: TypeScript
- **스타일 가이드**: ESLint 및 Prettier 규칙을 준수합니다.
- **네이밍**:
  - 컴포넌트: PascalCase (e.g., `NewsArticle`)
  - 변수/함수: camelCase (e.g., `fetchNews`)
  - 상수: UPPER_SNAKE_CASE (e.g., `API_KEY`)

## 2.2. Git 브랜치 전략
- `main`: 배포 가능한 안정 버전.
- `develop`: 다음 릴리스를 위한 개발 브랜치.
- `feature/이름`: 기능 개발 브랜치.

## 2.3. 커밋 메시지 규칙
- **형식**: `타입: 제목` (e.g., `feat: Add news feed component`)
- **타입 종류**:
  - `feat`: 새로운 기능 추가
  - `fix`: 버그 수정
  - `docs`: 문서 수정
  - `style`: 코드 스타일 변경 (포매팅 등)
  - `refactor`: 코드 리팩토링
  - `test`: 테스트 코드 추가/수정
