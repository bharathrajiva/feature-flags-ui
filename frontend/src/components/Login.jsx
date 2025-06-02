import React, { useEffect } from "react";
import { base64URLEncode, generateCodeVerifier, sha256 } from "../oauth";

const CLIENT_ID = import.meta.env.VITE_CLIENT_ID || "your-client-id";
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI || "http://localhost:5173/oauth/callback";
const AUTHORIZATION_ENDPOINT = import.meta.env.VITE_AUTHORIZATION_ENDPOINT || "http://localhost:8000/oauth/authorize";
const SCOPE = import.meta.env.VITE_SCOPE
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
export default function Login({ onToken }) {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");

 if (code) {
  const codeVerifier = localStorage.getItem("code_verifier");
  if (!codeVerifier) {
    alert("Code verifier missing");
    return;
  }

  // Send code and codeVerifier to backend
  fetch(`${BACKEND_URL}/oauth/callback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ code, codeVerifier, redirect_uri: REDIRECT_URI }),
  })
  .then(res => res.json())
  .then(data => {
    if (data.access_token) {
      onToken(data.access_token);
      localStorage.removeItem("code_verifier");
      window.history.replaceState({}, document.title, "/");
    } else {
      alert("Token exchange failed");
    }
  });
}

  }, [onToken]);

  async function login() {
    const codeVerifier = generateCodeVerifier();
    const codeChallengeBuffer = await sha256(codeVerifier);
    const codeChallenge = base64URLEncode(codeChallengeBuffer);
    localStorage.setItem("code_verifier", codeVerifier);
    const url = `${AUTHORIZATION_ENDPOINT}?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(
      REDIRECT_URI
    )}&scope=${encodeURIComponent(SCOPE)}&code_challenge=${codeChallenge}&code_challenge_method=S256`;
    window.location.href = url;
  }

  return (
    <div>
      <button onClick={login} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 2L9.5 7.5L12 15L14.5 7.5L12 2Z"
            fill="#E24329"
          />
          <path
            d="M7.5 7.5L5 12L7.5 15L10 7.5H7.5Z"
            fill="#FC6D26"
          />
          <path
            d="M16.5 7.5L19 12L16.5 15L14 7.5H16.5Z"
            fill="#FC6D26"
          />
          <path
            d="M12 15L10 22L14 22L12 15Z"
            fill="#FCA326"
          />
        </svg>
        Login with GitLab OAuth2
      </button>

    </div>
  );
}
