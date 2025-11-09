"""Authentication routes."""

from datetime import datetime, timedelta

import jwt
from aiohttp import web

from app.config import get_settings


def create_access_token(data: dict):
    """Create JWT token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.auth.jwt_expire_days)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.auth.jwt_secret, algorithm=settings.auth.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict | None:
    """Verify JWT token."""
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.auth.jwt_secret, algorithms=[settings.auth.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def login(request: web.Request) -> web.Response:
    """Login endpoint."""
    try:
        settings = get_settings()
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        if username == "admin" and password == settings.auth.admin_password:
            access_token = create_access_token({"sub": username})
            return web.json_response({
                "access_token": access_token,
                "token_type": "bearer",
                "username": "admin"
            })
        
        return web.json_response(
            {"error": "用户名或密码错误"},
            status=401
        )
    except Exception as e:
        return web.json_response(
            {"error": str(e)},
            status=400
        )


async def verify(request: web.Request) -> web.Response:
    """Verify token endpoint."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return web.json_response({"error": "未授权"}, status=401)
    
    token = auth_header[7:]
    payload = verify_token(token)
    
    if payload is None:
        return web.json_response({"error": "令牌无效或已过期"}, status=401)
    
    return web.json_response({
        "username": payload.get("sub"),
        "valid": True
    })


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """Authentication middleware."""
    # Skip auth for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await handler(request)
    
    # Skip auth for login and static files
    if request.path in ["/api/auth/login", "/api/auth/verify"] or not request.path.startswith("/api/"):
        return await handler(request)
    
    # Check authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return web.json_response({"error": "未授权"}, status=401)
    
    token = auth_header[7:]
    payload = verify_token(token)
    
    if payload is None:
        return web.json_response({"error": "令牌无效或已过期"}, status=401)
    
    # Add user info to request
    request["user"] = payload.get("sub")
    
    return await handler(request)


def setup_routes(app: web.Application):
    """Setup auth routes."""
    app.router.add_post("/api/auth/login", login)
    app.router.add_get("/api/auth/verify", verify)
