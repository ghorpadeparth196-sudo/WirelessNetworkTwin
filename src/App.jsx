import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "./api";
import Dashboard from "./components/Dashboard";
import APTable from "./components/APTable";
import UserTable from "./components/UserTable";
import Charts from "./components/Charts";
import { CoverageSummary } from "./components/NetworkStats";

const VIEWS = [
  { id: "overview", label: "Overview" },
  { id: "aps", label: "Access Points" },
  { id: "users", label: "Users" },
  { id: "analytics", label: "Analytics" },
];

const POLL_MS = 800; // how often the browser asks the backend for the newest state

export default function App() {
  const [view, setView] = useState("overview");
  const [campus, setCampus] = useState(null);
  const [state, setState] = useState(null);
  const [coverage, setCoverage] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const campusLoaded = useRef(false);

  // Fetch the newest simulation state (and the static campus layout once).
  const refresh = useCallback(async () => {
    try {
      if (!campusLoaded.current) {
        setCampus(await api.getCampus());
        campusLoaded.current = true;
      }
      setState(await api.getState());
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, POLL_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  // The coverage heat-map only changes when an AP is moved / switched, so it is
  // re-downloaded only when the backend's config_version changes.
  const configVersion = state ? state.config_version : null;
  useEffect(() => {
    if (configVersion === null) return;
    api.getCoverage().then(setCoverage).catch(() => {});
  }, [configVersion]);

  // Run a control action, then refresh immediately.
  const run = async (action) => {
    setBusy(true);
    try {
      await action();
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleMoveAP = async (id, x, y) => {
    try {
      await api.moveAccessPoint(id, x, y);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };
  const handleToggleAP = (id) => run(() => api.toggleAccessPoint(id));

  const running = state ? state.running : false;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-title">Digital Twin</div>
          <div className="brand-sub">Smart Campus Wi-Fi</div>
        </div>
        <nav>
          {VIEWS.map((v) => (
            <button key={v.id} className={`nav-item ${view === v.id ? "active" : ""}`} onClick={() => setView(v.id)}>
              {v.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          Signal strength is a <strong>simulated</strong> distance-based model, not a real RF measurement.
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <h1>Wireless Network Digital Twin</h1>
            <div className="subtitle">Smart Campus</div>
          </div>
          <div className="controls">
            <span className={`status-pill ${running ? "running" : "paused"}`}>
              {running ? "Running" : "Paused"}{state ? `, tick ${state.tick}` : ""}
            </span>
            <button className="btn btn-primary" disabled={!state || running || busy}
                    onClick={() => run(api.startSimulation)}>
              Start simulation
            </button>
            <button className="btn" disabled={!state || !running || busy}
                    onClick={() => run(api.pauseSimulation)}>
              Pause simulation
            </button>
            <button className="btn" disabled={!state || busy} onClick={() => run(api.resetSimulation)}>
              Reset simulation
            </button>
            <label className="speed">
              Speed
              <select value={state ? state.speed : 1} disabled={!state || busy}
                      onChange={(e) => run(() => api.setSpeed(Number(e.target.value)))}>
                <option value={0.5}>0.5x</option>
                <option value={1}>1x</option>
                <option value={2}>2x</option>
              </select>
            </label>
          </div>
        </header>

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        <main className="content">
          {!state ? (
            <div className="empty">{error ? "Waiting for the backend..." : "Connecting to the backend..."}</div>
          ) : (
            <>
              {view === "overview" && (
                <Dashboard state={state} campus={campus} coverage={coverage}
                           onMoveAP={handleMoveAP} onToggleAP={handleToggleAP} />
              )}
              {view === "aps" && (
                <>
                  <section className="panel">
                    <h2>Access points</h2>
                    <APTable aps={state.access_points} onToggle={handleToggleAP} />
                  </section>
                  <CoverageSummary coverage={state.stats.coverage} />
                </>
              )}
              {view === "users" && (
                <section className="panel">
                  <h2>Users</h2>
                  <UserTable users={state.users} />
                </section>
              )}
              {view === "analytics" && <Charts aps={state.access_points} history={state.history} />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
