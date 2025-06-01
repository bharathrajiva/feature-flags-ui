# backend/main.py

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import RootModel
from typing import Dict, List
import git_utils
import k8s_utils

app = FastAPI()

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
    if "review-mr" in env:
        try:
            flags_dict = k8s_utils.get_flags(project, env)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"K8s get failed: {e}")
    else:
        try:
            flags_dict = git_utils.read_flags(project, env, pat)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"GitLab get failed: {e}")

    if not flags_dict:
        raise HTTPException(status_code=404, detail="Flags not found")

    return flags_dict


@app.post("/flags/{project}/{env}")
def update_flags(
    project: str,
    env: str,
    request: FlagUpdateRequest,
    authorization: str = Header(...),
):
    pat = _extract_token(authorization)
    updates: Dict[str, dict] = request.model_dump()
    if "review-mr" in env:
        try:
            k8s_utils.patch_flags(namespace=env, flags_dict=updates)
            return {"status": "patched"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"K8s patch failed: {e}")

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


def _extract_token(authorization_header: str) -> str:
    if not authorization_header.lower().startswith("bearer "):
        raise HTTPException(status_code=400, detail="Authorization header must be: Bearer <PAT>")
    return authorization_header.split(None, 1)[1]
