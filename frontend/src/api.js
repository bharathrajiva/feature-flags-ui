const BASE_URL = "http://localhost:8000";

export async function getProjects(token) {
  const res = await fetch(`${BASE_URL}/projects`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function getEnvs(project, token) {
  const res = await fetch(`${BASE_URL}/projects/${project}/envs`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch envs");
  return res.json();
}

export async function getFlags(project, env, token) {
  const res = await fetch(`${BASE_URL}/flags/${project}/${env}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch flags");
  return res.json();
}

export async function updateFlags(project, env, flagsUpdate, token) {
  const res = await fetch(`${BASE_URL}/flags/${project}/${env}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(flagsUpdate),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to update flags");
  }
  return res.json();
}
export async function addFlags(project, flags, token) {
  const response = await fetch(`${BASE_URL}/add/flags/${project}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(flags),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to add flags");
  }
  return await response.json();
}
