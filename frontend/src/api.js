// Empty in local dev (Vite proxies /api to :8000). On Vercel set VITE_API_URL to your Render URL,
// e.g. https://site-control-room-api.onrender.com  (no trailing slash).
const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function j(res) {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const getSites = () => fetch(`${BASE}/api/sites`).then(j);
export const getSite = (id) => fetch(`${BASE}/api/sites/${id}`).then(j);
export const getSummary = (id, refresh = false) =>
  fetch(`${BASE}/api/sites/${id}/summary${refresh ? "?refresh=true" : ""}`).then(j);
export const ask = (question) =>
  fetch(`${BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  }).then(j);

export const STATUS = {
  on_track: { label: "On track", color: "#2e9e5b" },
  delayed: { label: "Delayed", color: "#d99a00" },
  at_risk: { label: "At risk", color: "#d64545" },
};

export const inr = (n) => {
  n = Number(n);
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(1)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
};
