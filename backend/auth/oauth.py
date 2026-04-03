"""
ScholarGraph AI — OAuth Integration
Google OAuth2 support for single sign-on.
"""

from typing import Optional
from pydantic import BaseModel


class OAuthConfig:
    """OAuth2 provider configuration."""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    @staticmethod
    def get_google_auth_url() -> str:
        """Generate Google OAuth2 authorization URL."""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": OAuthConfig.GOOGLE_CLIENT_ID,
            "redirect_uri": OAuthConfig.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query}"


class GoogleUserInfo(BaseModel):
    """Parsed Google OAuth user info."""
    email: str
    name: str
    picture: Optional[str] = None
    google_id: str
