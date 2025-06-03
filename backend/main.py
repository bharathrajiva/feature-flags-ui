from dotenv import load_dotenv
from fastapi import Query, FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import RootModel, BaseModel
from typing import Dict, List
import git_utils
import k8s_utils
import requests
import os

app = FastAPI()
load_dotenv()
# Secrets from env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://featureflags-ui.bee.secloredevops.com")
# Enable CORS, allowing exactly REDIRECT_URI as the origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[REDIRECT_URI],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class FlagUpdateRequest(RootModel[Dict[str, dict]]):
    """
    Expect a JSON body like:
    `{
        "fib-algo": {
            "variants": {
                "recursive": "recursive",
                "memo": "memo",
                "loop": "loop",
                "binet": "binet"
            },
            "defaultVariant": "binet",
            "state": "ENABLED"
        },
        "use-remote-fib-service": {
            "variants": {
                "on": true,
                "off": false
            },
            "defaultVariant": "off",
            "state": "ENABLED"
        },
        "super-variable-x": {
            "variants": {
                "on": true,
                "off": false
            },
            "defaultVariant": "off",
            "state": "ENABLED"
        },
        "release-custom-category": {
            "variants": {
                "on": true,
                "off": false
            },
            "defaultVariant": "off",
            "state": "ENABLED"
        }
    }`
    """
    pass

class OAuthCallbackRequest(BaseModel):
    code: str
    codeVerifier: str
    redirect_uri: str
# ----------------- UTILS ------------------
def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")
    return token

# ----------------- ROUTES ------------------

@app.get("/")
def root():
    return {"status": "ok"}

# OAuth2 PKCE callback
@app.post("/oauth/callback")
def oauth_callback(request: OAuthCallbackRequest = Body(...)):
    token_url = "https://gitlab.com/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": request.code,
        "grant_type": "authorization_code",
        "redirect_uri": request.redirect_uri,
        "code_verifier": request.codeVerifier,
    }
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=500, detail="Access token missing in response")

    redirect_resp = RedirectResponse(url="/", status_code=303)
    redirect_resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set True in production HTTPS
        samesite="Strict",
        max_age=3600,
        path="/"
    )
    return redirect_resp

# Optional: logout (clears cookie)
@app.post("/logout")
def logout():
    resp = RedirectResponse(url="/")
    resp.delete_cookie(key="access_token", path="/")
    return resp

@app.get("/userinfo")
def userinfo(request: Request) -> Dict:
    pat = get_token_from_cookie(request)
    url = "https://gitlab.com/api/v4/user" 
    headers = {"Authorization": f"Bearer {pat}"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch user info")
    user_data = response.json()
    return user_data   

@app.get("/projects", response_model=List[str])
def list_projects(request: Request):
    pat = get_token_from_cookie(request)
    return git_utils.get_projects(pat)

@app.get("/projects/{project}/envs", response_model=List[str])
def list_envs(project: str, request: Request):
    pat = get_token_from_cookie(request)
    envs = git_utils.get_envs(project, pat)
    if envs is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return envs

@app.get("/flags/{project}/{env}", response_model=Dict[str, dict])
def get_flags(project: str, env: str, request: Request):
    get_token_from_cookie(request)  # Auth check (token not needed by k8s)
    try:
        flags_dict = k8s_utils.get_flags(project, env)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"K8s get failed: {e}")
    if flags_dict is None:
        raise HTTPException(status_code=404, detail="Flags not found")
    return flags_dict

@app.put("/flags/{project}/{env}")
def update_flags(
    project: str,
    env: str,
    request_body: FlagUpdateRequest,
    request: Request
):
    pat = get_token_from_cookie(request)
    updates: Dict[str, dict] = request_body.model_dump()
    try:
        success = git_utils.safe_update_flags(project, env, updates, pat)
        if success:
            return {"status": "committed"}
        else:
            raise HTTPException(status_code=500, detail="GitLab update returned false")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/flags/{project}")
def add_flag(
    project: str,
    request_body: FlagUpdateRequest,
    request: Request
):
    pat = get_token_from_cookie(request)
    updates: Dict[str, dict] = request_body.model_dump()
    try:
        success = git_utils.add_flags_safe(project, updates, pat)
        if success:
            return {"status": "committed"}
        else:
            raise HTTPException(status_code=500, detail="GitLab add returned false")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
