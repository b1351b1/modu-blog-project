from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Post(Base):
    __tablename__ = "Post"
    
    post_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(255), nullable=False)  # "입시정보" or "영어지식"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    image_url = Column(String(500), nullable=True)
    
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    post_tags = relationship("PostTag", back_populates="post", cascade="all, delete-orphan")
    
    tags = relationship(
        "Tag",
        secondary="PostTag",
        back_populates="posts",
        viewonly=True
    )


class Tag(Base):
    __tablename__ = "Tag"
    
    tag_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    post_tags = relationship("PostTag", back_populates="tag", cascade="all, delete-orphan")
    
    posts = relationship(
        "Post",
        secondary="PostTag",
        back_populates="tags",
        viewonly=True
    )


class PostTag(Base):
    __tablename__ = "PostTag"
    
    post_tag_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("Post.post_id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("Tag.tag_id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint('post_id', 'tag_id', name='unique_post_tag'),
    )
    
    post = relationship("Post", back_populates="post_tags")
    tag = relationship("Tag", back_populates="post_tags")