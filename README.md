# 개인 캘린더 프로젝트

FastAPI와 PostgreSQL 기반 개인 캘린더입니다. 월별 달력, 월 이동, 오늘 표시, 날짜별 일정 조회 화면을 구현했습니다. 일정 입력·수정·삭제 화면은 다음 개발 단계입니다.

## 현재 PC에서 실행

프로젝트 폴더의 PowerShell 터미널에서 다음 명령을 실행합니다. 새 가상환경은 `.venv`입니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- 달력 화면: http://127.0.0.1:8000/
- API 사용 화면: http://127.0.0.1:8000/docs
- 월별 달력: http://127.0.0.1:8000/calendar/2026/10
- 종료: 실행 중인 터미널에서 Ctrl+C
- `start.ps1`로도 같은 서버를 실행할 수 있습니다.
- VS Code의 Python 인터프리터는 `.venv\Scripts\python.exe`를 선택합니다.
- HTML 파일을 더블클릭하거나 Live Server로 열지 않고, 위의 FastAPI 주소로 접속합니다. 같은 서버가 HTML/CSS/JS와 API를 함께 제공합니다.

## 새 PC에서 준비

1. Python 3.12와 PostgreSQL을 설치합니다. 현재 검증 환경은 Python 3.12 / PostgreSQL 18입니다.
2. PostgreSQL에 `calendar_db` 데이터베이스를 생성합니다.
3. 아래 명령으로 가상환경과 패키지를 준비합니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

4. `.env`의 `DATABASE_URL`에 실제 연결 정보를 입력합니다. 비밀번호에 `@`, `:`, `/`, `#` 같은 문자가 있으면 URL 인코딩이 필요합니다. 기존 `.env`가 있으면 덮어쓰지 마세요.
5. 위의 서버 실행 명령을 사용합니다. 서버가 시작될 때 `schedules` 테이블이 자동 생성됩니다.

현재 PC의 `.venv`는 제공된 Python 런타임으로 생성했습니다. 다른 PC로 `.venv`를 복사하지 말고 다시 생성하세요. 기존 `venv`는 이전 PC의 환경이므로 사용하지 않습니다.

## 설정과 API

- `.env`: 로컬 DB 연결 정보 및 네이버 API 인증정보. Git에서 제외됩니다.
- `.env.example`: 인증정보 없는 설정 양식. 시스템 환경변수가 `.env`보다 우선합니다.
- 네이버 키가 비어 있어도 장소 좌표 없이 일정을 저장할 수 있습니다.
- `GET /calendar/{year}/{month}`: 월요일 시작, 6주 42칸과 해당 기간 일정. 연도 1~9998, 월 1~12.
- `GET /schedules/`, `POST /schedules/`: 전체 일정 조회 / 생성.
- `PUT /schedules/{id}`, `DELETE /schedules/{id}`: 수정 / 삭제.

## 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
```

달력 테스트는 메모리 SQLite를 사용하므로 PostgreSQL의 실제 일정을 변경하지 않습니다.

## 남은 작업

- 화면에서 일정 추가·수정·삭제, 지도 표시.
- 공휴일 표시(현재는 토요일/일요일 색상만 구분).
- 과거 커밋에 포함된 인증정보 교체 및 Git에서 기존 `venv`, 캐시 파일 추적 해제. `.gitignore`만으로 이미 추적 중인 파일은 제외되지 않습니다.

## 달력 화면 설계와 코드 읽기

1. `frontend/index.html`: 월 이동 버튼, 7열 달력 표, 선택 날짜 상세 영역의 자리입니다. `defer`로 HTML 생성 후 JavaScript를 실행합니다.
2. `frontend/style.css`: 색상, 오늘/선택 날짜 구분, 일정 제목 말줄임, 모바일 배치를 담당합니다. 화면이 좁으면 상세 영역이 달력 아래로 이동합니다.
3. `frontend/app.js`: `state` → `loadCalendar()` → `renderCalendar()` → `renderAgenda()` 순서로 읽으면 데이터 흐름을 이해하기 쉽습니다. 주요 개념에 한국어 주석을 달았습니다.
4. `main.py`: `/`는 달력 HTML, `/static`은 CSS/JS를 제공합니다. `/calendar`와 `/schedules` API는 그대로 사용합니다.

화면을 열면 로컬 날짜 기준 현재 월을 요청합니다. Python이 계산한 42칸을 그대로 표시하므로 윤년과 앞뒤 달 날짜를 JavaScript에서 다시 계산하지 않습니다. 월 이동 시 해당 월의 1일을 선택하고, 오늘 버튼은 현재 월과 오늘 날짜로 돌아옵니다.

날짜 칸에는 일정 제목 최대 2개와 나머지 개수를 표시합니다. 날짜를 클릭하면 상세 영역에 그 날짜의 모든 일정 제목·분류·장소를 보여줍니다. 앞뒤 달의 회색 날짜도 선택할 수 있으며 보고 있는 월은 유지됩니다. 월별 일정 개수는 현재 월의 일정만 셉니다.

알아둘 구현 원칙:

- 보고 있는 월과 선택 날짜는 별개 상태입니다. 날짜 선택만 할 때는 이미 받은 데이터를 사용하므로 추가 API 요청이 없습니다.
- 오늘 날짜에 UTC 변환을 사용하지 않습니다. 한국의 새벽에 날짜가 하루 밀리는 오류를 방지합니다.
- 월 이동 요청이 겹치면 이전 요청을 취소하고 최신 응답만 반영합니다.
- 요청 중에는 이전 달 내용을 지우고 자리 표시자를 보여줍니다. 실패는 빈 일정과 구분하고 재시도 버튼을 제공합니다. 12초 이상 응답이 없으면 중단합니다.
- 일정 제목·장소는 `textContent`로 표시하여 입력 내용을 HTML로 실행하지 않습니다.
- 날짜 버튼은 키보드로도 선택할 수 있고, 선택 시 버튼을 재생성하지 않아 포커스를 유지합니다.

브라우저 검증: 42칸 표시, 다음 달 이동, 12월→1월 연도 전환, 오늘 복귀, 키보드 날짜 선택, 임시 일정 3개의 제목/분류/장소와 말줄임 표시, 390px 모바일 배치, 서버 연결 실패/재시도를 확인합니다. 테스트용 일정은 검증 후 삭제합니다.
