from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from database import get_db
from models.user import User
from utils.dependencies import get_current_user, create_token

router = APIRouter()

# 비밀번호 해싱을 위한 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic 스키마
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    nickname: str

class LoginRequest(BaseModel):
    name: str
    password: str

class UpdateProfileRequest(BaseModel):
    nickname: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    nickname: str
    role: str
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# 1. 회원가입 API
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    회원가입 API
    - name과 email은 unique해야 함
    - 비밀번호는 해싱 처리
    - 기본 role은 "user"
    """
    # name 중복 체크
    existing_user = db.query(User).filter(User.name == request.name).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이름입니다."
        )
    
    # email 중복 체크
    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다."
        )
    
    # 비밀번호 해싱
    hashed_password = pwd_context.hash(request.password)
    
    # 새 사용자 생성
    new_user = User(
        name=request.name,
        email=request.email,
        password=hashed_password,
        nickname=request.nickname,
        role="user"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user   # 반환된 new_user는 UserResponse 모델에 맞게 자동 변환됨


# 2. 로그인 API
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    로그인 API
    - name과 password로 인증
    - JWT 토큰 발급
    """
    # 사용자 조회
    user = db.query(User).filter(User.name == request.name).first()
    
    # 사용자가 없거나 비밀번호가 틀린 경우
    if not user or not pwd_context.verify(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 이름 또는 비밀번호입니다.",
            headers={"WWW-Authenticate": "Bearer"}  # Bearer 토큰이 필요하다는 표시
        )
    
    # JWT 토큰 생성
    access_token = create_token(user.user_id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# 3. 내 정보 조회 API
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    내 정보 조회 API
    - JWT 토큰 필요
    - 현재 로그인한 사용자 정보 반환
    """
    return current_user


# 4. 프로필 수정 API
@router.put("/profile", response_model=UserResponse)
def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    프로필 수정 API
    - JWT 토큰 필요
    - nickname만 수정 가능
    """
    current_user.nickname = request.nickname
    db.commit()
    db.refresh(current_user)
    
    return current_user


# 5. 비밀번호 변경 API
@router.put("/password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    비밀번호 변경 API
    - JWT 토큰 필요
    - 현재 비밀번호 검증 후 새 비밀번호로 변경
    """
    # 현재 비밀번호 검증
    if not pwd_context.verify(request.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다."
        )
    
    # 새 비밀번호 해싱 및 저장
    current_user.password = pwd_context.hash(request.new_password)
    db.commit()
    
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}