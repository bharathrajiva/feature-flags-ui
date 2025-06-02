from dotenv import load_dotenv
from fastapi import Query, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import RootModel, BaseModel
from typing import Dict, List
import git_utils
import k8s_utils
import requests
import os

app = FastAPI()
load_dotenv()

# Enable CORS (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth scheme for Swagger UI
security = HTTPBearer()

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

# Secrets from env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "gloas-92a7ebb4fa732e3b837f60c05f3c5dafb405b54e8f8fb738b5fafc1d1c7567f4")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://featureflags-ui.bee.secloredevops.com")

# Health check
@app.get("/")
def root():
    return {"status": "ok"}

# OAuth2 PKCE flow for GitLab
@app.post("/oauth/callback")
def oauth_callback(request: OAuthCallbackRequest):
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
    return {"access_token": token_data.get("access_token")}

# List projects
@app.get("/projects", response_model=List[str])
def list_projects(credentials: HTTPAuthorizationCredentials = Security(security)):
    pat = credentials.credentials
    return git_utils.get_projects(pat)

# List environments
@app.get("/projects/{project}/envs", response_model=List[str])
def list_envs(project: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    pat = credentials.credentials
    envs = git_utils.get_envs(project, pat)
    if envs is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return envs

# Get flags
@app.get("/flags/{project}/{env}", response_model=Dict[str, dict])
def get_flags(project: str, env: str, credentials: HTTPAuthorizationCredentials = Security(security)):
    pat = credentials.credentials
    try:
        flags_dict = k8s_utils.get_flags(project, env)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"K8s get failed: {e}")
    if flags_dict is None:
        raise HTTPException(status_code=404, detail="Flags not found")
    return flags_dict

# Update flags
@app.put("/flags/{project}/{env}")
def update_flags(
    project: str,
    env: str,
    request: FlagUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    pat = credentials.credentials
    updates: Dict[str, dict] = request.model_dump()
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

# Add flag
@app.post("/flags/{project}")
def add_flag(
    project: str,
    request: FlagUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    pat = credentials.credentials
    updates: Dict[str, dict] = request.model_dump()
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
