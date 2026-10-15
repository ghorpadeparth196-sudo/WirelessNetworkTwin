// All communication with the Flask backend lives in this one file.
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api";

async function request(path, options = {}) {
  const config = { ...options };
  if (options.body) config.headers = { "Content-Type": "application/json" };

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, config);
  } catch (err) {
    throw new Error(
      "Cannot reach the backend. Start the Flask server (python app.py) and keep it running on port 5000."
    );
  }

  let data = null;
  try {
    data = await response.json();
  } catch (err) {
    /* response had no JSON body */
  }
  if (!response.ok) {
    throw new Error((data && data.error) || `Request failed (${response.status})`);
  }
  return data;
}

export const getCampus = () => request("/campus");
export const getCoverage = () => request("/coverage");
export const getState = () => request("/simulation/state");
export const startSimulation = () => request("/simulation/start", { method: "POST" });
export const pauseSimulation = () => request("/simulation/pause", { method: "POST" });
export const resetSimulation = () => request("/simulation/reset", { method: "POST" });
export const setSpeed = (speed) =>
  request("/simulation/speed", { method: "POST", body: JSON.stringify({ speed }) });
export const moveAccessPoint = (id, x, y) =>
  request(`/access-points/${id}/position`, { method: "POST", body: JSON.stringify({ x, y }) });
export const toggleAccessPoint = (id) =>
  request(`/access-points/${id}/toggle`, { method: "POST" });
