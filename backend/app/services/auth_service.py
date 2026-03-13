from datetime import datetime, timedelta
from typing import Dict, Any
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.user import User


async def get_or_create_user(db: AsyncSession, google_user_info: Dict[str, Any]) -> User:
    """Get existing user by google_id or create a new one."""
    google_id = google_user_info.get("sub") or google_user_info.get("id")
    email = google_user_info.get("email")
    name = google_user_info.get("name")
    picture = google_user_info.get("picture")

    if not google_id or not email or not name:
        raise ValueError("Invalid Google user info: missing required fields")

    # Try to find existing user
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user:
        # Update user info if changed
        user.email = email
        user.name = name
        user.picture_url = picture
        await db.commit()
        await db.refresh(user)
    else:
        # Create new user
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            picture_url=picture,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user


def create_access_token(user_id: int) -> str:
    """Create a JWT access token for the user."""
    expires_at = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(db: AsyncSession, token: str) -> User | None:
    """Decode JWT token and return the current user."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user
    except (JWTError, ValueError, TypeError):
        return None


async def create_dev_user(db: AsyncSession) -> User:
    """Create or get a default dev user for local development."""
    result = await db.execute(select(User).where(User.google_id == "dev-user"))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            google_id="dev-user",
            email="dev@localhost",
            name="Dev User",
            picture_url=None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
