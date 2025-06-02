import React, { useState } from "react";
import Login from "./components/Login";
import Projects from "./components/Projects";
import Envs from "./components/Envs";
import Flags from "./components/Flags";

export default function App() {
  const [token, setToken] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedEnv, setSelectedEnv] = useState(null);

  if (!token) {
    return <Login onToken={setToken} />;
  }

  return (
    <div style={{ padding: "1rem" }}>
      <h1>Feature Flags Manager</h1>
      <button
        onClick={() => {
          setToken(null);
          setSelectedProject(null);
          setSelectedEnv(null);
        }}
      >
        Logout
      </button>

      <Projects token={token} onSelectProject={(p) => {
        setSelectedProject(p);
        setSelectedEnv(null);
      }} />

      <Envs
        token={token}
        project={selectedProject}
        onSelectEnv={setSelectedEnv}
      />

      <Flags
        token={token}
        project={selectedProject}
        env={selectedEnv}
      />
    </div>
  );
}
