# backend/main.py
from dotenv import load_dotenv
from fastapi import Query, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import RootModel
from typing import Dict, List
import git_utils
import k8s_utils
from pydantic import BaseModel
import requests
import os

app = FastAPI()

load_dotenv()

# Allow your React frontend (e.g. http://localhost:5173) to call this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, restrict to your frontend’s origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "gloas-92a7ebb4fa732e3b837f60c05f3c5dafb405b54e8f8fb738b5fafc1d1c7567f4")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://featureflags-ui.bee.secloredevops.com")

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/oauth/callback")
def oauth_callback(request: OAuthCallbackRequest):
    token_url = "https://gitlab.com/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": request.code,
        "grant_type": "authorization_code",
        "redirect_uri": request.redirect_uri,
        "code_verifier": request.codeVerifier,   # important for PKCE
    }
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)
    token_data = response.json()
    access_token = token_data.get("access_token")
    return {"access_token": access_token}

@app.get("/projects", response_model=List[str])
def list_projects(authorization: str = Header(...)):
    pat = _extract_token(authorization)
    return git_utils.get_projects(pat)


@app.get("/projects/{project}/envs", response_model=List[str])
def list_envs(project: str, authorization: str = Header(...)):
    pat = _extract_token(authorization)
    envs = git_utils.get_envs(project, pat)
    if envs is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return envs


@app.get("/flags/{project}/{env}", response_model=Dict[str, dict])
def get_flags(project: str, env: str, authorization: str = Header(...)):
    pat = _extract_token(authorization)
    # if "review-mr" in env:
    try:
        flags_dict = k8s_utils.get_flags(project, env)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"K8s get failed: {e}")
    # else:
    # try:
    #     flags_dict = git_utils.read_flags(project, env, pat)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"GitLab get failed: {e}")
    if flags_dict is None:
        raise HTTPException(status_code=404, detail="Flags not found")



    return flags_dict


@app.put("/flags/{project}/{env}")
def update_flags(
    project: str,
    env: str,
    request: FlagUpdateRequest,
    authorization: str = Header(...),
):
    pat = _extract_token(authorization)
    updates: Dict[str, dict] = request.model_dump()
    # if "review-mr" in env:
        # try:
        #     k8s_utils.patch_flags(project, env, updates)
        #     return {"status": "patched"}
        # except Exception as e:
        #     raise HTTPException(status_code=500, detail=f"K8s patch failed: {e}")

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
    request: FlagUpdateRequest,
    authorization: str = Header(...),
):
    pat = _extract_token(authorization)
    updates: Dict[str, dict] = request.model_dump()
    # if "review-mr" in env:
        # try:
        #     k8s_utils.patch_flags(project, env, updates)
        #     return {"status": "patched"}
        # except Exception as e:
        #     raise HTTPException(status_code=500, detail=f"K8s patch failed: {e}")
    
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

def _extract_token(authorization_header: str) -> str:
    if not authorization_header.lower().startswith("bearer "):
        raise HTTPException(status_code=400, detail="Authorization header must be: Bearer <PAT>")
    return authorization_header.split(None, 1)[1]
