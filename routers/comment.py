from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from database import get_db
from models.comment import Comment
from models.post import Post
from models.user import User
from utils.dependencies import get_current_user

router = APIRouter()


# Pydantic 스키마 정의
class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: str


# 헬퍼 함수: 게시글 존재 확인
def get_post_or_404(db: Session, post_id: int):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


# 헬퍼 함수: 댓글 존재 확인
def get_comment_or_404(db: Session, post_id: int, comment_id: int):
    comment = db.query(Comment).filter(
        Comment.comment_id == comment_id,
        Comment.post_id == post_id
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


# 헬퍼 함수: 작성자 권한 확인
def check_comment_author(comment: Comment, user: User):
    if comment.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")


# 헬퍼 함수: 댓글 응답 딕셔너리 생성
def make_comment_response(comment: Comment):
    return {
        "id": comment.comment_id,
        "content": comment.content,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "user": {
            "id": comment.user.user_id,
            "name": comment.user.name,
            "nickname": comment.user.nickname
        },
        "parent_id": comment.parent_comment_id,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at
    }


# 1. 댓글 작성
@router.post("/{post_id}/comments", status_code=201)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """게시글에 댓글 작성 (JWT 인증 필요)"""
    
    get_post_or_404(db, post_id)
    
    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.user_id,
        content=comment_data.content,
        parent_comment_id=None
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return make_comment_response(new_comment)


# 2. 댓글 목록 조회 (계층형 구조)
@router.get("/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """특정 게시글의 모든 댓글을 계층형 구조로 조회"""
    
    get_post_or_404(db, post_id)
    
    # 일반 댓글만 조회
    parent_comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_comment_id == None
    ).order_by(Comment.created_at.desc()).all()  # 최신 댓글이 제일 위로
    
    result = []
    
    for comment in parent_comments:
        # 대댓글 조회
        replies = db.query(Comment).filter(
            Comment.parent_comment_id == comment.comment_id # 현재 댓글의 ID를 보고 그 ID를 부모로 가진 댓글들을 찾아라
        ).order_by(Comment.created_at.asc()).all()
        
        # 대댓글 리스트 생성
        reply_list = [make_comment_response(reply) for reply in replies]
        
        # 댓글 + 대댓글 추가
        comment_dict = make_comment_response(comment)
        comment_dict["replies"] = reply_list
        result.append(comment_dict)
    
    total = db.query(Comment).filter(Comment.post_id == post_id).count()
    
    return {
        "post_id": post_id,
        "total": total,
        "comments": result
    }


# 3. 댓글 수정
@router.put("/{post_id}/comments/{comment_id}")
def update_comment(
    post_id: int,
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """댓글 수정 (JWT 인증 필요, 작성자만 가능)"""
    
    comment = get_comment_or_404(db, post_id, comment_id)
    check_comment_author(comment, current_user)
    
    comment.content = comment_data.content
    comment.updated_at = datetime.now()
    
    db.commit()
    db.refresh(comment)
    
    return make_comment_response(comment)


# 4. 댓글 삭제
@router.delete("/{post_id}/comments/{comment_id}")
def delete_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """댓글 삭제 (JWT 인증 필요, 작성자만 가능)"""
    
    comment = get_comment_or_404(db, post_id, comment_id)
    check_comment_author(comment, current_user)
    
    # 대댓글 개수 확인
    replies_count = db.query(Comment).filter(
        Comment.parent_comment_id == comment_id
    ).count()
    
    if replies_count > 0:
        # 대댓글이 있으면 내용만 변경
        comment.content = "삭제된 댓글입니다"
        comment.updated_at = datetime.now()
        db.commit()
        return {"message": "Comment content updated to deleted"}
    else:
        # 대댓글이 없으면 완전 삭제
        db.delete(comment)
        db.commit()
        return {"message": "Comment deleted successfully"}


# 5. 대댓글 작성
@router.post("/{post_id}/comments/{comment_id}/replies", status_code=201)
def create_reply(
    post_id: int,
    comment_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """대댓글 작성 (JWT 인증 필요, 1단계만 허용)"""
    
    get_post_or_404(db, post_id)
    parent_comment = get_comment_or_404(db, post_id, comment_id)
    
    # 대댓글의 대댓글 방지 (1단계 제한)
    if parent_comment.parent_comment_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot reply to a reply. Only one level of replies is allowed."
        )
    
    new_reply = Comment(
        post_id=post_id,
        user_id=current_user.user_id,
        content=comment_data.content,
        parent_comment_id=comment_id
    )
    
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    
    return make_comment_response(new_reply)