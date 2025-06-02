import React, { useEffect } from "react";
import { base64URLEncode, generateCodeVerifier, sha256 } from "../oauth";

const CLIENT_ID = "aff1324744305e745282f8822f75b4c0509d4aaea711bb709057bea49f15b454";
const REDIRECT_URI = "http://localhost:5173";
const AUTHORIZATION_ENDPOINT = "https://gitlab.com/oauth/authorize";
const SCOPE = "read_user api read_api";

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
  fetch(`http://localhost:8000/oauth/callback`, {
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
      <button onClick={login}>Login with OAuth2</button>
    </div>
  );
}
