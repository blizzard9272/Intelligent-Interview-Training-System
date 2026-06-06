"""
认证服务模块，定义了AuthService类，负责处理用户认证相关的业务逻辑。
主要功能包括：
1. 获取用户信息：提供根据邮箱、用户名或用户ID查询用户对象的方法。
2. 创建用户：提供一个方法，根据用户注册请求创建新的用户对象，并保存到数据库中。
3. 用户认证：提供一个方法，根据用户的邮箱和密码进行认证，如果认证成功，生成并返回JWT访问令牌，否则返回None。
4. 密码处理：在创建用户时，对密码进行哈希处理，确保安全存储；在认证过程中，验证用户输入的密码与存储的哈希密码是否匹配。
5. 依赖数据库会话：AuthService类在初始化时接受一个数据库会话对象，供其方法执行数据库操作使用，确保与数据库的交互能够正确进行。
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.auth import UserCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_user_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def create_user(self, payload: UserCreate) -> User:
        user = User(
            username=payload.username,
            email=payload.email,
            password_hash=get_password_hash(payload.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> str | None:
        user = self.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return create_access_token(str(user.id))
