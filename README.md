# 블로그 프로젝트

FastAPI 기반의 블로그 플랫폼 프로젝트입니다.

## 📌 프로젝트 개요

이 프로젝트는 JWT 인증, 게시글 CRUD, 댓글 기능, 문제 선택 기능을 포함한 종합 블로그 플랫폼입니다.

## 🛠 기술 스택

### Backend
- **Python**: 3.9+
- **FastAPI**: 웹 프레임워크
- **SQLAlchemy**: ORM
- **SQLite**: 데이터베이스
- **Redis**: 캐싱 및 인기 문제 추적
- **JWT**: 인증/인가

### Frontend
- **HTML/CSS/JavaScript**: UI 구현
- **Jinja2**: 템플릿 엔진

## 📁 프로젝트 구조

```
## 📁 프로젝트 구조
```
project/
├── main.py                 # FastAPI 애플리케이션 진입점
├── database.py             # 데이터베이스 연결 설정
├── requirements.txt        # 패키지 의존성
│
├── models/                 # SQLAlchemy 모델
│   ├── user.py
│   ├── problem.py
│   ├── post.py
│   └── comment.py
│
├── routers/                # API 라우터
│   ├── auth.py            # 인증 API
│   ├── problem.py         # 문제 관련 API
│   ├── blog.py            # 게시글 API
│   └── comment.py         # 댓글 API
│
├── utils/                  # 유틸리티 함수
│   └── dependencies.py    # JWT 인증 등
│
├── templates/              # HTML 템플릿
│   ├── intro.html
│   ├── index.html
│   ├── login.html
│   ├── join.html
│   ├── view.html
│   ├── write.html
│   ├── problem-select.html
│   ├── problem-register.html
│   └── mypage.html
│
├── static/                 # 정적 파일
│   ├── css/
│   │   ├── common.css
│   │   ├── intro.css
│   │   ├── list.css
│   │   ├── login-join.css
│   │   ├── view.css
│   │   ├── write.css
│   │   ├── table.css
│   │   ├── problem-select.css
│   │   ├── problem-register.css
│   │   └── mypage.css
│   └── img/
│       ├── icon-search.png
│       ├── first.png
│       ├── prev.png
│       ├── next.png
│       └── last.png
│
├── uploads/                # 업로드된 파일
│   ├── posts/             # 게시글 이미지
│   └── problems/          # 문제 파일
│
├── blog.db                # SQLite 데이터베이스
├── README.md             # 프로젝트 설명서
└── project_requirements.md

```

## 🚀 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력합니다:

```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=your-openai-api-key-here
```

### 4. 데이터베이스 초기화

애플리케이션을 처음 실행하면 SQLAlchemy가 자동으로 데이터베이스 테이블을 생성합니다.
또는 다음 코드를 `main.py`에 추가하여 수동으로 테이블을 생성할 수 있습니다:

```python
from database import engine, Base

# 애플리케이션 시작 시 테이블 생성
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
```

### 5. 서버 실행

```bash
uvicorn main:app --reload
```

서버가 실행되면 `http://localhost:8000`에서 접속 가능합니다.

## 📚 API 문서

FastAPI는 자동으로 API 문서를 생성합니다.

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 주요 기능

### 1. 인증 기능 (JWT)
- 회원가입 (`POST /auth/register`)
- 로그인 (`POST /auth/login`)
- 내 정보 조회 (`GET /auth/me`)
- 프로필 수정 (`PUT /auth/profile`)
- 비밀번호 변경 (`PUT /auth/password`)

### 2. 게시글 CRUD
- 게시글 작성 (`POST /blog`)
- 게시글 목록 조회 (`GET /blog`)
- 게시글 상세 조회 (`GET /blog/{post_id}`)
- 게시글 수정 (`PUT /blog/{post_id}`)
- 게시글 삭제 (`DELETE /blog/{post_id}`)
- 검색 및 필터링 기능
- 페이지네이션

### 3. 댓글 기능
- 댓글 작성 (`POST /blog/{post_id}/comments`)
- 댓글 목록 조회 (`GET /blog/{post_id}/comments`)
- 댓글 수정 (`PUT /blog/{post_id}/comments/{comment_id}`)
- 댓글 삭제 (`DELETE /blog/{post_id}/comments/{comment_id}`)
- 대댓글 작성 (`POST /blog/{post_id}/comments/{comment_id}/replies`)

### 4. 문제 선택 기능
- 문제 목록 조회 (`GET /problems`)
- 문제 선택 (`POST /problems/my`)
- 내가 선택한 문제 조회 (`GET /problems/my`)
- 문제 선택 취소 (`DELETE /problems/my/{id}`)
- 인기 문제 Top 10 조회 (`GET /problems/popular`)
- Redis 기반 캐싱 및 인기도 추적


## 🗄 데이터베이스 스키마

### User (사용자)

### Problem (문제)

### UserProblem (사용자-문제 선택)

### Post (게시글)

### Comment (댓글)

## 🔧 개발 가이드

### Git 브랜치 전략
- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발 브랜치

### 커밋 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드
chore: 빌드 업무, 패키지 관리
```

## 🧪 테스트

Postman을 사용하여 API 테스트를 진행합니다.

## 📅 개발 일정

**프로젝트 기간**: 2025년 10월 1일 ~ 10월 16일 

## 🐛 트러블슈팅

프로젝트 진행 중 발생한 주요 이슈와 해결 방법은 추후 업데이트됩니다.

