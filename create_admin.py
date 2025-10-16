from database import SessionLocal, engine, Base
from models.user import User
from models.post import Post, Tag, PostTag  
from models.comment import Comment  
from models.problem import Problem, UserProblem 
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    # 테이블이 없으면 생성
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 기존 admin 계정이 있는지 확인
        existing_admin = db.query(User).filter(User.name == "admin").first()
        
        if existing_admin:
            print("❌ 이미 admin 계정이 존재합니다.")
            print(f"   이메일: {existing_admin.email}")
            print(f"   닉네임: {existing_admin.nickname}")
            return
        
        # 관리자 계정 생성
        admin = User(
            name="admin",
            email="admin@example.com",
            password=pwd_context.hash("admin1234"),
            nickname="관리자",
            role="admin"
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ 관리자 계정이 생성되었습니다!")
        print("   아이디: admin")
        print("   비밀번호: admin1234")
        print("   이메일: admin@example.com")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()