"""
认证模块，定义了用户注册、登录和获取当前用户信息的API端点。
负责：
1. 用户注册：提供一个POST /register端点，接受用户的注册信息（用户名、邮箱和密码），并创建新的用户账户。
2. 用户登录：提供一个POST /login端点，接受用户的登录信息（邮箱和密码），验证用户身份，并返回JWT访问令牌。
3. 获取当前用户信息：提供一个GET /me端点，使用JWT令牌验证用户身份，并返回当前登录用户的详细信息。
4. 错误处理：在注册和登录过程中，如果发生错误（如邮箱已被注册、用户名已存在、邮箱或密码错误），返回适当的HTTP错误响应，提示用户相关问题。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    if service.get_user_by_email(payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被注册")
    if service.get_user_by_username(payload.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    return service.create_user(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    token = service.authenticate(payload.email, payload.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user
