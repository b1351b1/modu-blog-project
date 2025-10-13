from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Problem(Base):
    """문제 모델"""
    __tablename__ = "Problem"
    
    problem_id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    file_url = Column(String(500))
    difficulty = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 연도, 월, 번호 조합의 유니크 제약조건
    __table_args__ = (
        UniqueConstraint('year', 'month', 'number', name='unique_problem'),
    )
    
    user_problems = relationship("UserProblem", back_populates="problem", cascade="all, delete-orphan")


class UserProblem(Base):
    """사용자가 선택한 문제 모델"""
    __tablename__ = "UserProblem"
    
    user_problem_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.user_id'), nullable=False)
    problem_id = Column(Integer, ForeignKey('Problem.problem_id'), nullable=False)
    selection_count = Column(Integer, default=1)
    first_selected_at = Column(DateTime)
    last_selected_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 사용자와 문제 조합의 유니크 제약조건
    __table_args__ = (
        UniqueConstraint('user_id', 'problem_id', name='unique_user_problem'),
    )
    
    user = relationship("User", back_populates="user_problems")
    problem = relationship("Problem", back_populates="user_problems")