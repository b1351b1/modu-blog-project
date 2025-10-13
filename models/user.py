from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "User"
    
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False) 
    name = Column(String(255), unique=True, nullable=False, index=True) 
    nickname = Column(String(255), nullable=False)
    role = Column(String(50), default="user") 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    posts = relationship("Post", back_populates="author") 
    comments = relationship("Comment", back_populates="user")
    user_problems = relationship("UserProblem", back_populates="user")