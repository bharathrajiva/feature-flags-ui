export function base64URLEncode(str) {
  return btoa(String.fromCharCode.apply(null, new Uint8Array(str)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

export async function sha256(plain) {
  const encoder = new TextEncoder();
  const data = encoder.encode(plain);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return hash;
}

export function generateCodeVerifier() {
  const array = new Uint32Array(56/2);
  crypto.getRandomValues(array);
  return Array.from(array, dec => ("0" + dec.toString(16)).substr(-2)).join("");
}
