// Calls to the Python server - routes are documented in docs/ENDPOINTS.md.

async function request(path, options) {
  let res;
  try {
    res = await fetch(path, options);
  } catch {
    throw new Error("Can't reach the server. Is `python src/main.py serve` running?");
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail : `Server error (${res.status})`);
  }
  return body;
}

export const getConfig = () => request("/api/config");

export function analyze(file, labels, settings) {
  const form = new FormData();
  form.append("file", file);
  if (labels) form.append("labels", labels);
  form.append("conf", settings.conf);
  form.append("num_zones", settings.numZones);
  form.append("horizon_y", settings.horizonY);
  return request("/api/analyze", { method: "POST", body: form });
}
