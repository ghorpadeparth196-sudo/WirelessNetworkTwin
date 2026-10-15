import { formatDbm } from "../utils";

// The 8 summary cards at the top of the dashboard.
export default function NetworkStats({ stats }) {
  const pct = (a, b) => (b ? `${Math.round((a / b) * 100)}% of users` : "");
  const cards = [
    { label: "Total Access Points", value: stats.total_aps, note: `${stats.online_aps} online`, tone: "" },
    { label: "Total Users", value: stats.total_users, note: "virtual students", tone: "" },
    { label: "Connected Users", value: stats.connected_users, note: pct(stats.connected_users, stats.total_users), tone: "good" },
    { label: "Disconnected Users", value: stats.disconnected_users, note: "outside any coverage",
      tone: stats.disconnected_users > 0 ? "warn" : "good" },
    { label: "Average Signal Strength", value: formatDbm(stats.avg_signal), note: "connected users", tone: "" },
    { label: "Average Network Utilization", value: `${stats.avg_utilization}%`, note: `busiest AP ${stats.max_utilization}%`,
      tone: stats.avg_utilization >= 80 ? "bad" : stats.avg_utilization >= 50 ? "warn" : "good" },
    { label: "Congested APs", value: stats.congested_aps, note: "High or Overloaded",
      tone: stats.congested_aps > 0 ? "bad" : "good" },
    { label: "Weak-Signal Users", value: stats.weak_signal_users, note: "signal in the Weak band",
      tone: stats.weak_signal_users > 0 ? "warn" : "good" },
  ];

  return (
    <div className="cards">
      {cards.map((c) => (
        <div key={c.label} className={`card tone-${c.tone || "plain"}`}>
          <div className="card-label">{c.label}</div>
          <div className="card-value">{c.value}</div>
          <div className="card-note">{c.note}</div>
        </div>
      ))}
    </div>
  );
}

// Weak-signal area detection: coverage per building / open area.
export function CoverageSummary({ coverage }) {
  if (!coverage) return null;
  return (
    <section className="panel">
      <h2>Coverage analysis</h2>
      <p className="muted small">
        Campus coverage {coverage.coverage_percent}%. Weak or no signal in {coverage.weak_area_percent}% of the campus.
      </p>
      <ul className="zone-list">
        {coverage.zones.map((z) => (
          <li key={z.id}>
            <div className="zone-row">
              <span>{z.name}</span>
              <span className={`badge ${z.weak_area_percent >= 50 ? "badge-high" : "badge-normal"}`}>
                {z.weak_area_percent >= 50 ? "Weak area" : "Good"}
              </span>
            </div>
            <div className="bar">
              <span className="fill fill-weak" style={{ width: `${z.weak_area_percent}%` }} />
            </div>
            <div className="muted small">{z.weak_area_percent}% weak or no signal</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
