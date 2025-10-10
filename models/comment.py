from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Comment(Base):
    __tablename__ = "Comment"
    
    comment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("Post.post_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("Comment.comment_id"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    # 댓글이 속한 게시글
    post = relationship("Post", back_populates="comments")
    
    # 댓글 작성자
    user = relationship("User", back_populates="comments")
    
    # 부모 댓글 (대댓글인 경우)
    parent = relationship("Comment", remote_side=[comment_id], back_populates="replies")
    
    # 자식 댓글들 (이 댓글에 달린 대댓글들)
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")