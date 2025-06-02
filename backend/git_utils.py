# backend/git_utils.py
import os
import requests
import yaml
import threading
from fastapi import HTTPException

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

GITLAB_API_BASE = "https://gitlab.com/api/v4"
FLAGS_REPO_PATH_WITH_NAMESPACE = "bee26401516/projects/flags"
FLAG_PAT = "glpat-M8Lb62BTcWqMj5KZom27"
# e.g. "mygroup/flags" or "your-username/flags"
# This is the GitLab “path_with_namespace” for your flags repo.

BRANCH = "master"
# The branch in which your feature-flags-patch.yaml files live (e.g. "main" or "master").

# ─── THREADING LOCKS ────────────────────────────────────────────────────────────

# We keep a per-(project, env) lock so that two requests trying to update the same
# file don’t both do GET→PUT at the exact same time.
_locks: dict[str, threading.Lock] = {}
_locks_mutex = threading.Lock()

def _get_lock(project: str, env: str) -> threading.Lock:
    key = f"{project}-{env}"
    with _locks_mutex:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def _encode_path(project: str, env: str, type: str) -> str:
    """
    Convert "expense-manager-backend/alpha/feature-flags-patch.yaml"
    into URL-encoded form "expense-manager-backend%2Falpha%2Ffeature-flags-patch.yaml"
    """
    if type == "put":
        raw_path = f"{project}/{env}/feature-flags-patch.yaml"
    else:
        raw_path = f"{project}/{env}/feature-flags.yaml"

    return raw_path.replace("/", "%2F")


def _get_project_id(pat: str) -> int:
    """
    Fetch the numeric project ID of the flags repo (FLAGS_REPO_PATH_WITH_NAMESPACE)
    via the GitLab API:
      GET /projects/:url_encoded_path
    """
    # GitLab expects the path (including slashes) to be URL-encoded:
    encoded = FLAGS_REPO_PATH_WITH_NAMESPACE.replace("/", "%2F")
    url = f"{GITLAB_API_BASE}/projects/{encoded}"
    headers = {"Authorization": f"Bearer {FLAG_PAT}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()["id"]


def _get_file_metadata(project_id: int, encoded_path: str, pat: str) -> dict:
    """
    Fetches JSON metadata for a file, which includes last_commit_id.
    GET /projects/:id/repository/files/:encoded_path?ref=<BRANCH>
    """
    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/files/{encoded_path}"
    headers = {"Authorization": f"Bearer {FLAG_PAT}"}
    params = {"ref": BRANCH}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.json()


def _get_raw_file(project_id: int, encoded_path: str, pat: str) -> str:
    """
    GET /projects/:id/repository/files/:encoded_path/raw?ref=<BRANCH>
    Returns the raw YAML as text.
    """
    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/files/{encoded_path}/raw"
    headers = {"Authorization": f"Bearer {FLAG_PAT}"}
    params = {"ref": BRANCH}
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.json())
    return r.text


def _merge_flag_changes(original_yaml: str, updates: dict[str, dict]) -> str:
    """
    Given the original YAML (string) and updates = {flagName: bool, ...},
    produce a new YAML string where each flag’s value is replaced/inserted.
    We assume feature-flags-patch.yaml has this shape:
      flags:
        FF_LOGIN_BUTTON: true
        FF_NEW_UI: false
    """
    data = yaml.safe_load(original_yaml) or {}
    if "spec" not in data or not isinstance(data["spec"], dict):
        data["spec"] = {}

    if "flagSpec" not in data["spec"] or not isinstance(data["spec"]["flagSpec"], dict):
        data["spec"]["flagSpec"] = {}

    if "flags" not in data["spec"]["flagSpec"] or not isinstance(data["spec"]["flagSpec"]["flags"], dict):
        data["spec"]["flagSpec"]["flags"] = {}

    for flag_name, flag_value in updates.items():
        data["spec"]["flagSpec"]["flags"][flag_name] = flag_value
    return yaml.safe_dump(data)


def _put_file(project_id: int, encoded_path: str, pat: str, new_content: str, last_commit_id: str, updates: dict[str, dict]) -> requests.Response:
    """
    PUT /projects/:id/repository/files/:encoded_path
    with JSON body:
      {
        "branch": BRANCH,
        "content": "<base64 or plain YAML>",
        "commit_message": "Update feature flags",
        "last_commit_id": "<SHA>",
      }
    """
    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/files/{encoded_path}"
    headers = {
        "Authorization": f"Bearer {FLAG_PAT}",
        "Content-Type": "application/json"
    }
    updated_keys = list(updates.keys())
    flag_summary = ", ".join(updated_keys[:5]) + ("..." if len(updated_keys) > 5 else "")
    env = yaml.safe_load(new_content)["metadata"]["name"]
    username = get_user_details_and_permissions(pat).get("user", {}).get("username", "Unknown User")
    commit_message = f"chore(@{username}): {env} updated {len(updated_keys)} flags ({flag_summary})"

    payload = {
        "branch": BRANCH,
        "content": new_content,
        "commit_message": commit_message,
        "last_commit_id": last_commit_id
    }
    return requests.put(url, headers=headers, json=payload)


# ─── PUBLIC FUNCTIONS ──────────────────────────────────────────────────────────

def get_all_projects(pat: str) -> list[str]:
    """
    List the top-level folders (project names) in the flags repo.
    We:
      1) Determine the numeric project ID of FLAGS_REPO_PATH_WITH_NAMESPACE.
      2) List the repo tree at depth=1 (so we only see top-level folders).
         GET /projects/:id/repository/tree?ref=<BRANCH>&per_page=100
      3) Return the list of names where `type == "tree"`.
    """
    project_id = _get_project_id(pat)
    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/tree"
    headers = {"Authorization": f"Bearer {FLAG_PAT}"}
    params = {"ref": BRANCH, "per_page": 100}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    result = []
    for entry in resp.json():
        if entry["type"] == "tree":
            result.append(entry["name"])
    return result

def get_projects(pat: str) -> list[str]:
    """
    List top-level folders (project names) in the flags repo with pagination.
    """
    project_id = _get_project_id(pat)
    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/tree"
    headers = {"Authorization": f"Bearer {FLAG_PAT}"}

    page = 1
    result = []
    user_data = get_user_details_and_permissions(pat)
    if not user_data:
        raise HTTPException(status_code=404, detail="User data not found")
    user_projects = user_data.get("projects", [])
    if not user_projects:
        raise HTTPException(status_code=404, detail="No projects found for the user")
    # Filter projects based on user permissions
    user_project_names = {project["name"] for project in user_projects}
    if not user_project_names:
        raise HTTPException(status_code=404, detail="No accessible projects found for the user")

    while True:
        params = {"ref": BRANCH, "per_page": 100, "page": page}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.json())

        data = resp.json()
        if not data:
            break

        result.extend(entry["name"] for entry in data if entry["type"] == "tree")
        page += 1
    # print(f"Found {len(result)} projects in the flags repo.")
    # print(f"User {user_data.get("user").get("name")} has access to {len(user_project_names)} projects.")
    # Filter result to only include projects the user has access to
    result = [name for name in result if name in user_project_names]
    if not result:
        raise HTTPException(status_code=404, detail="No accessible projects found in the flags repo")
    # print(f"Accessible projects after filtering: {result}")
    # Return the filtered list of project names
    return result

def get_envs(project: str, pat: str) -> list[str] | None:
    """
    Lists subfolders of a given top-level folder (e.g. 'expense-manager-backend') with pagination.
    Filters to only environments the user has access to via CODEOWNERS and that match naming patterns.
    Returns None if the project path doesn't exist.
    """
    project_id = _get_project_id(pat)
    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/tree"
    headers = {"Authorization": f"Bearer {FLAG_PAT}"}

    # Get user info
    user_data = get_user_details_and_permissions(pat)
    if not user_data:
        raise HTTPException(status_code=404, detail="User data not found")

    username = user_data.get("user", {}).get("username", "Unknown User")
    username_tag = f"@{username}"

    # Get CODEOWNERS data
    code_owners_data = code_owners(pat)

    # Extract paths the user has access to
    envs_accessible = [
        path for path, owners in code_owners_data.items()
        if username_tag in owners
    ]

    print(f"User {username} has access to the following environments: {envs_accessible}")

    # # If user has no access to any envs, return empty list
    # if not envs_accessible:
    #     return []

    result = []
    page = 1

    # Fetch folder list with pagination
    while True:
        params = {"ref": BRANCH, "path": project, "per_page": 100, "page": page}
        resp = requests.get(url, headers=headers, params=params)

        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.json())

        data = resp.json()
        if not data:
            break

        # Filter subfolders (trees) that are named alpha/beta/ci/nightly
        result.extend(
            entry["name"]
            for entry in data
            if entry["type"] == "tree"
            and entry["name"] != "_template"
        )
        page += 1

    # Only include folders the user has access to
        filtered_result = []
        has_full_access = "*" in envs_accessible or f"/{project}/*" in envs_accessible
        for env in result:
            is_special_env = any(pattern in env for pattern in ["-alpha", "-beta", "-ci", "-nightly"])

            if has_full_access:
                # User has full access — include everything
                filtered_result.append(env)
            elif not is_special_env:
                print(f"User {username} has limited access to {env}.")
                # User has limited access — include only non-special envs
                filtered_result.append(env)

    return filtered_result


def read_flags(project: str, env: str, pat: str) -> dict[str, bool] or None:
    """
    Fetch and parse feature-flags-patch.yaml for (project, env).
    Returns a Python dict {flagName: bool, ...} or None if not found.
    """
    project_id = _get_project_id(pat)
    encoded_path = _encode_path(project, env, "get")

    # GET raw YAML
    try:
        raw_yaml = _get_raw_file(project_id, encoded_path, pat)
    except HTTPException as he:
        if he.status_code == 404:
            return None
        raise

    # Parse YAML, return {flag: bool}
    data = yaml.safe_load(raw_yaml) or {}
    # Ensure it’s a dict under “flags”
    return data.get("spec", {}).get("flagSpec", {}).get("flags", {})


def update_flags_via_gitlab(project: str, env: str, updates: dict[str, dict], pat: str) -> bool:
    """
    1) GET the file metadata (to learn last_commit_id).
    2) GET raw YAML.
    3) Merge in user updates.
    4) PUT with last_commit_id. If 409, return False so caller can retry.
    """
    project_id = _get_project_id(pat)
    encoded_path = _encode_path(project, env, "put")

    # 1) Metadata
    meta = _get_file_metadata(project_id, encoded_path, pat)
    last_commit_id = meta["last_commit_id"]

    # 2) Raw YAML
    original_yaml = _get_raw_file(project_id, encoded_path, pat)

    # 3) Merge
    new_yaml = _merge_flag_changes(original_yaml, updates)

    # 4) Attempt PUT
    resp = _put_file(project_id, encoded_path, pat, new_yaml, last_commit_id, updates)
    if resp.status_code == 200:
        return True
    if resp.status_code == 409:
        # Conflict → caller may retry once more
        return False

    # Some other error
    raise HTTPException(status_code=resp.status_code, detail=resp.json())


def safe_update_flags(project: str, env: str, updates: dict[str, bool], pat: str) -> bool:
    """
    1) Acquire (project, env) lock so only one thread is updating that file at a time.
    2) Call update_flags_via_gitlab():
       - If it returns True → done.
       - If False (409 Conflict) → re-fetch and retry exactly once.
    Returns True if committed, or raises HTTPException on unrecoverable errors.
    """
    lock = _get_lock(project, env)
    with lock:
        # First attempt
        success = update_flags_via_gitlab(project, env, updates, pat)
        if success:
            return True

        # Conflict → retry once
        success_retry = update_flags_via_gitlab(project, env, updates, pat)
        if success_retry:
            return True

        # If still conflict → raise error
        raise HTTPException(
            status_code=409,
            detail="Conflict updating flags. Please fetch the latest and try again."
        )
def get_user_details_and_permissions(pat: str) -> dict:
    """
    Fetch GitLab user info and their project permissions using their personal access token (PAT).
    Supports pagination for listing all projects.
    """
    headers = {"Authorization": f"Bearer {pat}"}

    # 1. Get user info
    user_resp = requests.get(f"{GITLAB_API_BASE}/user", headers=headers)
    if user_resp.status_code != 200:
        raise Exception(f"Failed to get user: {user_resp.json()}")

    user_data = user_resp.json()

    # 2. Get all projects with pagination
    page = 1
    projects = []

    while True:
        params = {
            "membership": True,
            "per_page": 100,
            "page": page
        }
        projects_resp = requests.get(f"{GITLAB_API_BASE}/projects", headers=headers, params=params)
        if projects_resp.status_code != 200:
            raise Exception(f"Failed to get projects: {projects_resp.json()}")

        data = projects_resp.json()
        if not data:
            break

        for project in data:
            projects.append({
                "name": project["name"],
                "path_with_namespace": project["path_with_namespace"],
                "permissions": project.get("permissions", {})
            })

        page += 1

    return {
        "user": user_data,
        "projects": projects
    }
def code_owners(FLAG_PAT: str) -> dict:
    """
    Fetch the CODEOWNERS file from the flags repo.
    Returns a dictionary mapping file paths to their owners.
    """
    project_id = _get_project_id(FLAG_PAT)
    encoded_path = "CODEOWNERS".replace("/", "%2F")

    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/files/{encoded_path}/raw"
    headers = {"Authorization": f"Bearer {FLAG_PAT}"}
    params = {"ref": BRANCH}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    codeowners_content = response.text
    codeowners_dict = {}

    for line in codeowners_content.splitlines():
        if line.strip() and not line.startswith("#"):
            parts = line.split()
            if len(parts) > 1:
                path = parts[0]
                owners = parts[1:]
                codeowners_dict[path] = owners

    return codeowners_dict

def _encode_flags_yaml_path(project: str) -> str:
    """
    Encode the path for the flags.yaml file at the project root, e.g.:
    "expense-manager-backend/flags.yaml" → URL encoded
    """
    raw_path = f"{project}/flags.yaml"
    return raw_path.replace("/", "%2F")


def _merge_flags_yaml(original_yaml: str, updates: dict[str, dict]) -> str:
    """
    Merge updates into flags.yaml structure.

    Assuming flags.yaml has a structure like:
    flags:
    flag-name:
        variants:
        variant-key: variant-value
        defaultVariant: someVariant
        state: ENABLED|DISABLED


    Updates is a dict of {flagName: dict}
    """
    data = yaml.safe_load(original_yaml) or {}
    if "flags" not in data or not isinstance(data["flags"], dict):
        data["flags"] = {}

    for flag_name, flag_value in updates.items():
        data["flags"][flag_name] = flag_value

    return yaml.safe_dump(data)


def add_flags(project: str, updates: dict[str, bool], pat: str) -> bool:
    """
    Adds or updates flags in {project}/flags.yaml in the GitLab repo.

    Steps:
    1) GET metadata (last_commit_id)
    2) GET raw flags.yaml content
    3) Merge updates into flags.yaml content
    4) PUT updated content with last_commit_id
    5) Return True if successful, False if 409 conflict (caller can retry)

    Raises HTTPException on other errors.
    """
    project_id = _get_project_id(pat)
    encoded_path = _encode_flags_yaml_path(project)

    # 1) Get file metadata (last_commit_id)
    meta = _get_file_metadata(project_id, encoded_path, pat)
    last_commit_id = meta["last_commit_id"]

    # 2) Get raw YAML content
    original_yaml = _get_raw_file(project_id, encoded_path, pat)

    # 3) Merge flag updates
    new_yaml = _merge_flags_yaml(original_yaml, updates)

    # 4) PUT updated file
    url = f"{GITLAB_API_BASE}/projects/{project_id}/repository/files/{encoded_path}"
    headers = {
        "Authorization": f"Bearer {FLAG_PAT}",
        "Content-Type": "application/json"
    }

    updated_keys = list(updates.keys())
    user_details = get_user_details_and_permissions(pat)
    username = user_details.get("user", {}).get("username", "Unknown User")
    username_tag = f"@{username}"

    # Get CODEOWNERS data
    code_owners_data = code_owners(pat)

    # Extract paths the user has access to
    projects_accessible = [
        path for path, owners in code_owners_data.items()
        if username_tag in owners
    ]
    has_full_access = "*" in projects_accessible or f"/{project}/*" in projects_accessible

    if not username:
        raise HTTPException(status_code=404, detail="User not found")

    flag_summary = ", ".join(updated_keys[:5]) + ("..." if len(updated_keys) > 5 else "")
    commit_message = f"chore(@{username}): adds {len(updated_keys)} flags ({flag_summary})"


    payload = {
        "branch": BRANCH,
        "content": new_yaml,
        "commit_message": commit_message,
        "last_commit_id": last_commit_id,
    }
    # print(payload.get("content"))
    if has_full_access:
        # User has full access — proceed with PUT
        resp = requests.put(url, headers=headers, json=payload)
        if resp.status_code == 200:
            return True
        if resp.status_code == 409:
            return False  # conflict, caller can retry
        raise HTTPException(status_code=resp.status_code, detail=resp.json())
    else:
        raise HTTPException(
            status_code=403,
            detail=f"User @{username} does not have permission to update flags in {project}. "
                   f"Please contact a project owner or admin."
        )
    

def add_flags_safe(project: str, updates: dict[str, bool], pat: str) -> bool:
    """
    Safely add or update flags in {project}/flags.yaml with locking.
    Acquires a lock for the (project) to prevent concurrent updates.
    Retries once if a conflict occurs.
    """
    lock = _get_lock(project, "flags")
    with lock:
        success = add_flags(project, updates, pat)
        if success:
            return True
        # Conflict → retry once
        success_retry = add_flags(project, updates, pat)
        if success_retry:
            return True
        raise HTTPException(
            status_code=409,
            detail="Conflict updating flags. Please fetch the latest and try again."
        )
# print(add_flags_safe("expense-manager-backend", {"sample-flag-3": {"variants": {"on": True, "off": False}, "defaultVariant": "off", "state": "ENABLED"}}, "glpat-M8Lb62BTcWqMj5KZom27"))

# print(get_envs("expense-manager-backend", "glpat-M8Lb62BTcWqMj5KZom27"))
# print(code_owners("glpat-M8Lb62BTcWqMj5KZom27"))
# print(get_projects("glpat-M8Lb62BTcWqMj5KZom27"))
# print(get_user_details_and_permissions("glpat-M8Lb62BTcWqMj5KZom27"))
# print(safe_update_flags("expense-manager-backend", "beta", {"release-custom-category": {"state": "ENABLED", "defaultVariant": "on", "variants": {"on": True, "off": False}}, "use-remote-fib-service": {"variants": {"on": True, "off": False}, 'defaultVariant': 'off', 'state': 'DISABLED'}}, "glpat-af"))