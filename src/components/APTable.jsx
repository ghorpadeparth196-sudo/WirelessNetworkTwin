import { formatDbm } from "../utils";

// Table of all access points with load, signal and an on/off what-if switch.
export default function APTable({ aps, onToggle }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>AP ID</th>
            <th>AP Name</th>
            <th>Location</th>
            <th className="num">Connected Users</th>
            <th className="num">Capacity</th>
            <th>Utilization</th>
            <th className="num">Average Signal</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {aps.map((ap) => {
            const level = ap.congestion.toLowerCase();
            return (
              <tr key={ap.id}>
                <td><strong>{ap.id}</strong></td>
                <td>{ap.name}</td>
                <td>{ap.location}</td>
                <td className="num">{ap.connected_users}</td>
                <td className="num">{ap.capacity}</td>
                <td>
                  <div className="util-cell">
                    <div className="bar">
                      <span className={`fill fill-${level}`} style={{ width: `${Math.min(100, ap.utilization)}%` }} />
                    </div>
                    <span>{ap.utilization}%</span>
                  </div>
                </td>
                <td className="num">{formatDbm(ap.avg_signal)}</td>
                <td><span className={`badge badge-${level}`}>{ap.congestion}</span></td>
                <td>
                  <button className="btn btn-small" onClick={() => onToggle(ap.id)}>
                    {ap.online ? "Turn off" : "Turn on"}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
