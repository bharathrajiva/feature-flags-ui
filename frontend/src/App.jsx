import React, { useState, useEffect } from "react";
import Login from "./components/Login";
import Projects from "./components/Projects";
import Envs from "./components/Envs";
import Flags from "./components/Flags";

export default function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState(null); // <-- add username state
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedEnv, setSelectedEnv] = useState(null);

  // Fetch user info when token is set
  useEffect(() => {
    if (!token) {
      setUsername(null);
      return;
    }

    fetch("https://gitlab.com/api/v4/user", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch user");
        return res.json();
      })
      .then((user) => setUsername(user.username))
      .catch(() => setUsername(null));
  }, [token]);

  if (!token) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          width: "100vw",
        }}
      >
        <div style={{ textAlign: "center", color: "#eee" }}>
          <Login onToken={setToken} />
        </div>
      </div>
    );
  }

  const containerStyle = {
    margin: "0 auto",
    padding: "2rem",
    justifyContent: "center",
    alignItems: "center",
    height: "90vh",
    width: "95vw",
  };

  const headerStyle = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "1.5rem",
  };

  const buttonStyle = {
    padding: "0.5rem 1rem",
    fontWeight: "600",
    backgroundColor: "#121212",
    color: "white",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    transition: "background-color 0.3s ease",
  };

  const sectionStyle = {
    maxWidth: "100%",
    marginBottom: "2rem",
    padding: "1rem",
    backgroundColor: "#1E1E1E",
    borderRadius: "6px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
  };

  const disabledOverlay = {
    pointerEvents: "none",
    opacity: 0.5,
  };

  return (
    <div style={containerStyle}>
      <header style={headerStyle}>
        <h1 style={{ margin: 0, fontWeight: "700" }}>
          Feature Flags Manager
          {username && (
            <span style={{ marginLeft: "1rem", fontWeight: "400", fontSize: "1.2rem" }}>
              — Welcome, @{username}
            </span>
          )}
        </h1>

        <button
          onClick={() => {
            setToken(null);
            setSelectedProject(null);
            setSelectedEnv(null);
            setUsername(null);
          }}
          style={buttonStyle}
        >
          Logout
        </button>
      </header>

      <section style={sectionStyle}>
        <Projects
          token={token}
          onSelectProject={(p) => {
            setSelectedProject(p);
            setSelectedEnv(null);
          }}
        />
      </section>

      <section
        style={{
          ...sectionStyle,
          ...(selectedProject ? {} : disabledOverlay),
        }}
      >
        <h2 style={{ marginTop: 0, color: "#ddd" }}>Environments</h2>
        {selectedProject ? (
          <Envs
            token={token}
            project={selectedProject}
            onSelectEnv={setSelectedEnv}
          />
        ) : (
          <p style={{ color: "#999" }}>Select a project to see environments</p>
        )}
      </section>

      <section
        style={{
          ...sectionStyle,
          ...(selectedEnv ? {} : disabledOverlay),
        }}
      >
        <h2 style={{ marginTop: 0, color: "#ddd" }}>Flags</h2>
        {selectedEnv ? (
          <Flags token={token} project={selectedProject} env={selectedEnv} />
        ) : (
          <p style={{ color: "#999" }}>
            Select an environment to view and manage flags
          </p>
        )}
      </section>
    </div>
  );
}
