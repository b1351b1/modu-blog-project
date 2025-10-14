from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import os
from routers import comment 
from models.user import User
from models.post import Post, Tag, PostTag
from models.comment import Comment
from models.problem import Problem, UserProblem


# FastAPI 앱 생성
app = FastAPI()

# CORS 설정 (프론트엔드와 백엔드가 다른 포트에서 실행될 경우)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용하도록 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 애플리케이션 시작 시 데이터베이스 테이블 자동 생성
# 모든 모델이 임포트된 후 실행됩니다
Base.metadata.create_all(bind=engine)

# 정적 파일 서빙 설정
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 라우터 임포트 및 등록 (나중에 추가)
from routers import auth, blog, comment, problem
app.include_router(auth.router, prefix="/auth", tags=["인증"])
app.include_router(blog.router, prefix="/blog", tags=["게시글"])
app.include_router(problem.router, prefix="/problems", tags=["문제"])
app.include_router(comment.router, prefix="/blog", tags=["댓글"])

# 루트 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "블로그 프로젝트 API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# 헬스 체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)