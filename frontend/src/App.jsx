import React, { useState, useEffect } from "react";
import Login from "./components/Login";
import Projects from "./components/Projects";
import Envs from "./components/Envs";
import Flags from "./components/Flags";
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export default function App() {
  const [username, setUsername] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedEnv, setSelectedEnv] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Fetch user info on mount or after login/logout
  useEffect(() => {
    setLoadingUser(true);
    fetch(`${BACKEND_URL}/userinfo`, {
      credentials: "include", // Send cookies
    })
      .then((res) => {
        if (!res.ok) throw new Error("Not authenticated");
        return res.json();
      })
      .then((data) => {
        setUsername(data.username);
      })
      .catch(() => {
        setUsername(null);
      })
      .finally(() => setLoadingUser(false));
  }, []);

  if (loadingUser) {
    return <div>Loading...</div>;
  }

  if (!username) {
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
          <Login />
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

  const logout = () => {
    fetch(`${BACKEND_URL}/logout`, {
      method: "POST",
      credentials: "include", // Send cookies
    }).then(() => {
      setUsername(null);
      setSelectedProject(null);
      setSelectedEnv(null);
    });
  };

  return (
    <div style={containerStyle}>
      <header style={headerStyle}>
        <h1 style={{ margin: 0, fontWeight: "700" }}>
          Feature Flags Manager
          {username && (
            <span
              style={{
                marginLeft: "1rem",
                fontWeight: "400",
                fontSize: "1.2rem",
                display: "inline-block",
                whiteSpace: "nowrap",
              }}
            >
              — Welcome, @{username}
            </span>
          )}
        </h1>
        <button onClick={logout} style={buttonStyle}>
          Logout
        </button>
      </header>

      <section style={sectionStyle}>
        <Projects
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
          <Envs project={selectedProject} onSelectEnv={setSelectedEnv} />
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
          <Flags project={selectedProject} env={selectedEnv} />
        ) : (
          <p style={{ color: "#999" }}>
            Select an environment to view and manage flags
          </p>
        )}
      </section>
    </div>
  );
}
