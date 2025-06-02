import React, { useEffect, useState } from "react";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
const selectStyle = {
  width: "100%",
  maxWidth: "500px",
  padding: "8px 12px",
  fontSize: "16px",
  borderRadius: "6px",
  border: "1.5px solid #ccc",
  backgroundColor: "#121212",
  cursor: "pointer",
  transition: "border-color 0.3s",
};

const containerStyle = {
  margin: "1em 0",
};

export default function Envs({ token, project, onSelectEnv }) {
  const [envs, setEnvs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!project) return;

    async function load() {
      setLoading(true);
      try {
        const res = await fetch(
          `${BACKEND_URL}/projects/${project}/envs`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!res.ok) throw new Error("Failed to load envs");
        const data = await res.json();
        setEnvs(data);
      } catch (e) {
        alert(e.message);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [project, token]);

  if (!project) return null;

  return (
    <div style={containerStyle}>
      <h3 style={{ marginBottom: "8px" }}>Environments for {project}</h3>
      {loading && <p>Loading environments...</p>}
      {!loading && (
        <select
          defaultValue=""
          style={selectStyle}
          onChange={(e) => onSelectEnv(e.target.value)}
          onFocus={(e) => (e.target.style.borderColor = "#007bff")}
          onBlur={(e) => (e.target.style.borderColor = "#ccc")}
        >
          <option value="" disabled>
            Select an environment
          </option>
          {envs.map((env) => (
            <option key={env} value={env}>
              {env}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
