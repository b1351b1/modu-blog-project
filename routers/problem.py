from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db, redis_client
from models.problem import Problem, UserProblem
from models.user import User
from utils.dependencies import get_current_user, get_current_admin
import os
import shutil

router = APIRouter()

# 파일 업로드 디렉토리 설정
UPLOAD_DIR = "uploads/problems"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic 스키마
class ProblemResponse(BaseModel):
    problem_id: int
    year: int
    month: int
    number: int
    title: str
    difficulty: Optional[str]
    file_url: Optional[str]
    
    class Config:
        from_attributes = True

class UserProblemResponse(BaseModel):
    user_problem_id: int
    user_id: int
    problem_id: int
    selection_count: int
    first_selected_at: Optional[datetime]
    last_selected_at: Optional[datetime]
    created_at: datetime
    problem: ProblemResponse
    
    class Config:
        from_attributes = True

class ProblemListResponse(BaseModel):
    total: int
    page: int
    limit: int
    problems: List[ProblemResponse]

class MyProblemListResponse(BaseModel):
    total: int
    page: int
    limit: int
    my_problems: List[UserProblemResponse]

class SelectProblemRequest(BaseModel):
    problem_id: int

class PopularProblemResponse(BaseModel):
    problem_id: int
    year: int
    month: int
    number: int
    title: str
    difficulty: str
    selection_count: int


# 1. 관리자 전용 문제 등록 API
@router.post("/admin/problems", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
async def create_problem(
    year: int = Form(...),
    month: int = Form(...),
    number: int = Form(...),
    title: str = Form(...),
    difficulty: str = Form(...),
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    관리자 전용 문제 등록 API
    - 파일 업로드 지원 (한글/PDF/PNG)
    - year, month, number 조합은 unique해야 함
    - month는 3, 6, 9, 11만 허용
    """
    # 월 검증
    if month not in [3, 6, 9, 11]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="3,6,9,11월만 문제 등록이 가능합니다."
        )
    
    # 중복 체크
    existing_problem = db.query(Problem).filter(
        Problem.year == year,
        Problem.month == month,
        Problem.number == number
    ).first()
    
    if existing_problem:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="문제가 이미 존재합니다."
        )
    
    # 파일 확장자 검증
    allowed_extensions = ['.hwp', '.pdf', '.png', '.jpg', '.jpeg']
    file_extension = os.path.splitext(file.filename)[1].lower() # 파일명과 확장자 분리시켜서 확장자만 선택하고 소문자 처리
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다. 업로드 가능한 파일 형식: {', '.join(allowed_extensions)}" # 리스트의 요소들을 합쳐서 하나의 문자열로 만듦
        )
    
    # 파일 저장
    file_name = f"{year}_{month}_{number}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer: # 업로드된 파일을 바이너리 쓰기 모드로 열기 (파일을 열어서 buffer라는 이름으로 사용)
        shutil.copyfileobj(file.file, buffer) # 업로드된 파일의 내용을 버퍼에 복사 (파일 저장)
    
    # 문제 생성
    new_problem = Problem(
        year=year,
        month=month,
        number=number,
        title=title,
        difficulty=difficulty,
        file_url=f"/{file_path}"
    )
    
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)
    
    return new_problem


# 2. 문제 목록 조회 API
@router.get("/", response_model=ProblemListResponse)
def get_problems(
    year: Optional[int] = None,
    month: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    문제 목록 조회 API
    - year, month로 필터링 가능
    - 페이지네이션 지원
    """
    query = db.query(Problem)
    
    # 필터링
    if year:
        query = query.filter(Problem.year == year)
    if month:
        query = query.filter(Problem.month == month)
    
    # 총 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    problems = query.order_by(Problem.year.desc(), Problem.month.desc(), Problem.number).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "problems": problems
    }


# 3. 문제 선택 API (내 문제에 추가)
@router.post("/my", response_model=UserProblemResponse, status_code=status.HTTP_201_CREATED)
def select_problem(
    request: SelectProblemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    문제 선택 API
    - 특정 문제를 내 문제 목록에 추가
    - 이미 선택한 문제면 selection_count 증가
    """
    # 문제 존재 확인
    problem = db.query(Problem).filter(Problem.problem_id == request.problem_id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문제를 찾을 수 없습니다."
        )
    
    # 이미 선택한 문제인지 확인
    user_problem = db.query(UserProblem).filter(
        UserProblem.user_id == current_user.user_id,
        UserProblem.problem_id == request.problem_id
    ).first()
    
    if user_problem:
        # 이미 선택한 문제면 카운트 증가
        user_problem.selection_count += 1
        user_problem.last_selected_at = datetime.utcnow()
    else:
        # 새로 선택
        user_problem = UserProblem(
            user_id=current_user.user_id,
            problem_id=request.problem_id,
            selection_count=1,
            first_selected_at=datetime.utcnow(),
            last_selected_at=datetime.utcnow()
        )
        db.add(user_problem)
    
    db.commit()
    db.refresh(user_problem)
    
    # Redis에 인기도 카운트 증가
    if redis_client:
        redis_client.zincrby("popular_problems", 1, request.problem_id)
    
    return user_problem


# 4. 내가 선택한 문제 조회 API
@router.get("/my", response_model=MyProblemListResponse)
def get_my_problems(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내가 선택한 문제 조회 API (마이페이지)
    - 페이지네이션 지원
    """
    query = db.query(UserProblem).filter(UserProblem.user_id == current_user.user_id)
    
    # 총 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    my_problems = query.order_by(UserProblem.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "my_problems": my_problems
    }


# 5. 문제 선택 취소 API
@router.delete("/my/{user_problem_id}")
def delete_my_problem(
    user_problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    문제 선택 취소 API
    - 내 문제 목록에서 삭제
    - 본인이 선택한 문제만 삭제 가능
    """
    user_problem = db.query(UserProblem).filter(
        UserProblem.user_problem_id == user_problem_id
    ).first()
    
    if not user_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="선택된 문제가 없습니다."
        )
    
    # 권한 체크
    if user_problem.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="문제를 삭제할 권한이 없습니다."
        )
    
    problem_id = user_problem.problem_id
    
    # 삭제
    db.delete(user_problem)
    db.commit()
    
    # Redis에서 인기도 카운트 감소
    if redis_client:
        redis_client.zincrby("popular_problems", -1, problem_id)
    
    return {"message": "문제가 내 문제 목록에서 삭제되었습니다."}


# 6. 인기 문제 Top 10 조회 API
@router.get("/popular")
def get_popular_problems(db: Session = Depends(get_db)):
    """
    인기 문제 Top 10 조회 API
    - Redis 캐싱 활용
    """
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis 서버에 연결할 수 없습니다."
        )
    
    # Redis에서 인기 문제 Top 10 조회 (점수 높은 순)
    popular_problem_ids = redis_client.zrevrange("popular_problems", 0, 9, withscores=True)
    
    if not popular_problem_ids:
        return {"popular_problems": []}
    
    # DB에서 문제 정보 조회
    popular_problems = []
    for problem_id, selection_count in popular_problem_ids: # Redis에서 가져온 데이터는 전부 문자열
        problem = db.query(Problem).filter(Problem.problem_id == int(problem_id)).first()
        if problem:
            popular_problems.append({
                "problem_id": problem.problem_id,
                "year": problem.year,
                "month": problem.month,
                "number": problem.number,
                "title": problem.title,
                "difficulty": problem.difficulty,
                "selection_count": int(selection_count)
            })
    
    return {"popular_problems": popular_problems}