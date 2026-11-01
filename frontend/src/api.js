async function j(res) {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const getSites = () => fetch("/api/sites").then(j);
export const getSite = (id) => fetch(`/api/sites/${id}`).then(j);
export const getSummary = (id, refresh = false) =>
  fetch(`/api/sites/${id}/summary${refresh ? "?refresh=true" : ""}`).then(j);
export const ask = (question) =>
  fetch("/api/ask", {
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
