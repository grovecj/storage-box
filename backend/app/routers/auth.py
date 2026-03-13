from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from app.config import settings
from app.database import get_db
from app.schemas.user import UserResponse, TokenResponse
from app.services import auth_service
from app.dependencies import get_current_user
import httpx

router = APIRouter(prefix="/auth", tags=["auth"])

# Configure OAuth
oauth = OAuth()
if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


@router.get("/google")
async def google_login():
    """Redirect to Google OAuth consent screen."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    redirect_uri = f"{settings.app_base_url}/api/v1/auth/google/callback"
    authorization_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
    )
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback, exchange code for tokens, and return JWT."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")

    redirect_uri = f"{settings.app_base_url}/api/v1/auth/google/callback"

    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        # Get user info from Google
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if user_info_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        google_user_info = user_info_response.json()

    # Create or update user in our database
    user = await auth_service.get_or_create_user(db, google_user_info)

    # Create our own JWT
    jwt_token = auth_service.create_access_token(user.id)

    # Redirect to frontend with token
    frontend_url = f"{settings.app_base_url}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/me", response_model=UserResponse)
async def get_me(user = Depends(get_current_user)):
    """Get current authenticated user."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side only - just clear token)."""
    return {"message": "Logged out successfully"}


@router.get("/dev-token")
async def get_dev_token(db: AsyncSession = Depends(get_db)):
    """Get a dev token for local development (only works when OAuth is not configured)."""
    if settings.google_client_id and settings.google_client_secret:
        raise HTTPException(status_code=403, detail="Dev token only available in dev mode")

    user = await auth_service.create_dev_user(db)
    token = auth_service.create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
