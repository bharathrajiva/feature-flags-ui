const BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export async function getProjects() {
  const res = await fetch(`${BASE_URL}/projects`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function getEnvs(project) {
  const res = await fetch(`${BASE_URL}/projects/${project}/envs`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch envs");
  return res.json();
}

export async function getFlags(project, env) {
  const res = await fetch(`${BASE_URL}/flags/${project}/${env}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch flags");
  return res.json();
}

export async function updateFlags(project, env, flagsUpdate) {
  const res = await fetch(`${BASE_URL}/flags/${project}/${env}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(flagsUpdate),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update flags");
  }
  return res.json();
}

export async function addFlags(project, flags) {
  const response = await fetch(`${BASE_URL}/flags/${project}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(flags),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to add flags");
  }
  return await response.json();
}
