from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from database import get_db
from models.post import Post, Tag, PostTag
from models.user import User
from utils.dependencies import get_current_admin

router = APIRouter()


class CategoryEnum(str, Enum):
    ADMISSION = "입시정보"
    ENGLISH = "영어지식"
    
class PostCreate(BaseModel):
    title: str
    content: str
    category: CategoryEnum
    tags: list[str] = []  # 자유롭게 태그 입력


def make_post_response(post: Post):
    """게시글 응답 딕셔너리 생성"""
    return {
        "id": post.post_id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "author_id": post.user_id,
        "author": {
            "id": post.author.user_id,
            "name": post.author.name,
            "nickname": post.author.nickname
        },
        "tags": [tag.name for tag in post.tags],
        "created_at": post.created_at,
        "updated_at": post.updated_at
    }


def handle_tags(db: Session, post: Post, tag_names: list[str], timestamp: str):
    
    # 새 태그 추가
    for tag_name in tag_names:
        tag_name = tag_name.strip()
        if not tag_name:
            continue
        
        # 태그가 이미 있는지 확인
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        
        # 없으면 새로 만들기
        if not tag:
            tag = Tag(name=tag_name, created_at=timestamp)
            db.add(tag)
            db.flush() # 임시저장
        
        # 게시글-태그 연결
        post_tag = PostTag(
            post_id=post.post_id,
            tag_id=tag.tag_id,
            created_at=timestamp
        )
        db.add(post_tag)


# ===== 1. 게시글 작성 (관리자만) =====
@router.post("", status_code=201)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    게시글 작성 - 관리자 전용
    """
    
    # 현재 시간
    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 게시글 생성
    new_post = Post(
        user_id=current_user.user_id,
        title=post_data.title,
        content=post_data.content,
        category=post_data.category.value,
        created_at=created_at,
        updated_at=created_at
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # 태그 처리
    if post_data.tags:
        handle_tags(db, new_post, post_data.tags, created_at)
        db.commit()
        db.refresh(new_post)
    
    # 응답 반환
    return make_post_response(new_post)


# ===== 2. 게시글 목록, 검색 =====
@router.get("")
def get_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[CategoryEnum] = None,
    sort: str = Query("desc"),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    게시글 목록 조회 및 검색
    """
    # 기본 쿼리
    query = db.query(Post)
    
    # 검색어가 있으면 필터링
    if search:
        # 제목이나 내용에서 검색
        query = query.filter(
            (Post.title.contains(search)) | (Post.content.contains(search))
        )
    
    # 카테고리 필터
    if category:
        query = query.filter(Post.category == category.value)
    
    # 정렬 (최신순/오래된순)
    if sort == "desc":
        query = query.order_by(Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.asc())
    
    # 전체 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    posts = query.offset(offset).limit(limit).all()
    
    # 응답 생성
    result = {
        "total": total,
        "page": page,
        "limit": limit,
        "posts": [make_post_response(post) for post in posts]
    }
    
    # 검색어가 있으면 추가
    if search:
        result["keyword"] = search
    
    return result


# ===== 3. 태그별 게시글 조회 =====
@router.get("/tags/{tag_name}")
def get_posts_by_tag(
    tag_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("desc"),
    db: Session = Depends(get_db)
):
    """
    특정 태그의 게시글 목록 조회
    """
    # 태그 찾기
    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    
    if not tag:
        raise HTTPException(status_code=404, detail="태그를 찾을 수 없습니다.")
    
    # 태그에 연결된 게시글 찾기
    query = db.query(Post).join(PostTag).filter(PostTag.tag_id == tag.tag_id)
    
    # 정렬 (데이터베이스 정렬)
    if sort == "desc":
        query = query.order_by(Post.created_at.desc())
    else:
        query = query.order_by(Post.created_at.asc())
    
    # 전체 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    posts = query.offset(offset).limit(limit).all()
    
    # 응답 생성
    return {
        "tag": tag_name,
        "total": total,
        "page": page,
        "limit": limit,
        "posts": [make_post_response(post) for post in posts]
    }