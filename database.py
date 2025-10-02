from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# SQLite 데이터베이스 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

# SQLAlchemy 엔진 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 세션 로컬 클래스 생성
SessionLocal = sessionmaker(bind=engine)

# Base 클래스 생성 (모든 모델의 부모 클래스)
Base = declarative_base()

# Redis 연결 설정 (캐싱 및 인기 문제 추적용)
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
    # Redis 연결 테스트
    redis_client.ping()
    print("Redis 연결 성공!")
except redis.ConnectionError:
    print("Redis 연결 실패! Redis 서버가 실행 중인지 확인하세요.")
    redis_client = None

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()