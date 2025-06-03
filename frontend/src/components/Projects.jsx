import React, { useEffect, useState } from "react";

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

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export default function Projects({ onSelectProject }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await fetch(`${BACKEND_URL}/projects`, {
          credentials: "include", // <- Important: sends the HttpOnly cookie
        });
        if (!res.ok) throw new Error("Failed to load projects");
        const data = await res.json();
        setProjects(data);
      } catch (e) {
        alert(e.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []); // <- no token dependency

  return (
    <div style={containerStyle}>
      <h2 style={{ marginBottom: "8px" }}>Projects</h2>
      {loading && <p>Loading projects...</p>}
      {!loading && (
        <select
          defaultValue=""
          style={selectStyle}
          onChange={(e) => onSelectProject(e.target.value)}
          onFocus={(e) => (e.target.style.borderColor = "#fff")}
          onBlur={(e) => (e.target.style.borderColor = "#fff")}
        >
          <option value="" disabled>
            Select a project
          </option>
          {projects.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
