"""Google OAuth/SSO Integration"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import httpx, urllib.parse
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["oauth"])

REDIRECT_URI = "https://nexusai-backend-production-f2e2.up.railway.app/api/auth/google/callback"

@router.get("/google")
def google_login():
    if not settings.google_client_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=503,
            detail="Google OAuth not configured. Add GOOGLE_CLIENT_ID to Railway Variables.")
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=select_account"
    )
    print(f"🔐 OAuth redirect_uri: {REDIRECT_URI}")
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None):
    fe = settings.frontend_url or "https://nexusai-frontend-nine.vercel.app"

    if error or not code:
        print(f"❌ OAuth cancelled or error: {error}")
        return RedirectResponse(f"{fe}/login?error=google_cancelled")

    if not settings.google_client_id:
        return RedirectResponse(f"{fe}/login?error=oauth_not_configured")

    print(f"🔄 Token exchange with redirect_uri: {REDIRECT_URI}")
    async with httpx.AsyncClient() as client:
        tok_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )
        print(f"🔑 Token response status: {tok_resp.status_code}")
        if tok_resp.status_code != 200:
            print(f"❌ Token error: {tok_resp.text}")
            return RedirectResponse(f"{fe}/login?error=token_exchange_failed")

        tok = tok_resp.json()
        ui = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tok['access_token']}"}
        )
        if ui.status_code != 200:
            return RedirectResponse(f"{fe}/login?error=userinfo_failed")
        g = ui.json()

    from app.core.auth import create_access_token
    name = g.get("name", g["email"].split("@")[0])
    user = {
        "email": g["email"], "name": name, "role": "employee",
        "departments": ["general"], "features": ["chat"],
        "initials": "".join([w[0] for w in name.split()[:2]]).upper(),
        "oauth": "google"
    }
    token = create_access_token(user)
    print(f"✅ Google login success: {g['email']}")
    return RedirectResponse(
        f"{fe}/login?oauth_token={token}"
        f"&oauth_name={urllib.parse.quote(name)}"
        f"&oauth_email={urllib.parse.quote(g['email'])}"
    )
