"""
依赖项模块，定义了获取当前用户和数据库会话的依赖项函数。
负责：
1. 获取当前用户：通过解析JWT令牌获取用户信息，并从数据库中查询用户对象。
2. 获取数据库会话session：提供一个生成器函数，返回数据库会话对象，供其他依赖项或路由处理函数使用。
3. 处理认证异常：如果令牌无效或用户不存在，抛出HTTP 401 Unauthorized异常，提示认证失败。
4. OAuthh2 token URL配置：使用FastAPI的OAuth2PasswordBearer类配置令牌获取的URL路径，方便前端进行认证请求。
"""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败",
    )
    try:
        # 从token中解码获取用户信息
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    # 根据用户ID从数据库中查询用户对象
    user = AuthService(db).get_user_by_id(int(user_id))
    if not user:
        raise credentials_exception
    return user

# 定义数据库会话的类型提示
DbSession = Generator[Session, None, None]
