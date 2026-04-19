from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.core.auth import authenticate_user, create_access_token, verify_token
from app.core.rbac import ROLES, DEPARTMENTS, get_departments, has_feature, DEMO_USERS
from app.models.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = verify_token(token)
    return payload

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user)
    role_meta = ROLES.get(user["role"], {})
    return LoginResponse(
        access_token=token,
        user={**user,
              "role_label": role_meta.get("label", user["role"]),
              "role_color": role_meta.get("color", "#818cf8"),
              "role_icon": role_meta.get("icon", "user"),
              "departments": get_departments(user["role"]),
              "features": role_meta.get("features", []),
        }
    )

@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role", "employee")
    role_meta = ROLES.get(role, {})
    return {**current_user,
            "role_label": role_meta.get("label", role),
            "role_color": role_meta.get("color", "#818cf8"),
            "departments": get_departments(role),
            "features": role_meta.get("features", []),
    }

@router.get("/demo-users")
def demo_users():
    return [{"email": e, "role": u["role"], "name": u["name"]} for e, u in DEMO_USERS.items()]
