// Live alert list produced by the backend on every tick.
export default function Alerts({ alerts }) {
  const count = (level) => alerts.filter((a) => a.level === level).length;
  return (
    <section className="panel">
      <h2>
        Alerts
        <span className="alert-counts">
          <span className="badge badge-overloaded">{count("critical")} critical</span>
          <span className="badge badge-high">{count("warning")} warning</span>
        </span>
      </h2>
      <ul className="alert-list">
        {alerts.length === 0 && <li className="muted">No alerts.</li>}
        {alerts.map((a, i) => (
          <li key={`${i}-${a.message}`} className={`alert alert-${a.level}`}>
            {a.message}
          </li>
        ))}
      </ul>
    </section>
  );
}
