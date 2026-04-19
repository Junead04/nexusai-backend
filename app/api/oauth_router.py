"""Google OAuth/SSO Integration"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import httpx, os
from app.core.config import Settings  # fresh instance each call

router = APIRouter(prefix="/auth", tags=["oauth"])

def _cfg():
    """Always read fresh from .env — no caching."""
    return Settings()

@router.get("/google")
def google_login():
    cfg = _cfg()
    if not cfg.google_client_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Google OAuth not configured. Add GOOGLE_CLIENT_ID to backend/.env")
    redirect_uri = f"{cfg.backend_url}/api/auth/google/callback"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={cfg.google_client_id}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=select_account"
    )
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None):
    cfg = _cfg()
    fe = cfg.frontend_url

    if error or not code:
        return RedirectResponse(f"{fe}/login?error=google_cancelled")
    if not cfg.google_client_id:
        return RedirectResponse(f"{fe}/login?error=oauth_not_configured")

    redirect_uri = f"{cfg.backend_url}/api/auth/google/callback"
    async with httpx.AsyncClient() as client:
        tok = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code, "client_id": cfg.google_client_id,
            "client_secret": cfg.google_client_secret,
            "redirect_uri": redirect_uri, "grant_type": "authorization_code",
        })
        if tok.status_code != 200:
            return RedirectResponse(f"{fe}/login?error=token_exchange_failed")

        ui = await client.get("https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tok.json()['access_token']}"})
        if ui.status_code != 200:
            return RedirectResponse(f"{fe}/login?error=userinfo_failed")
        g = ui.json()

    from app.core.auth import create_access_token
    import urllib.parse
    name = g.get("name", g["email"].split("@")[0])
    user = {"email": g["email"], "name": name, "role": "employee",
            "departments": ["general"], "features": ["chat"],
            "initials": "".join([w[0] for w in name.split()[:2]]).upper(),
            "oauth": "google"}
    token = create_access_token(user)
    return RedirectResponse(
        f"{fe}/login?oauth_token={token}"
        f"&oauth_name={urllib.parse.quote(name)}"
        f"&oauth_email={urllib.parse.quote(g['email'])}"
    )
