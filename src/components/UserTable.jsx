import { useState } from "react";
import { formatDbm, qualityColor } from "../utils";

// Table of all users, with a simple search box and status filter.
export default function UserTable({ users }) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const visible = users.filter((u) => {
    if (filter === "connected" && u.status !== "Connected") return false;
    if (filter === "disconnected" && u.status !== "Disconnected") return false;
    if (filter === "weak" && u.quality !== "Weak") return false;
    const text = `${u.id} ${u.name}`.toLowerCase();
    return text.includes(search.trim().toLowerCase());
  });

  return (
    <div>
      <div className="table-tools">
        <input
          type="search"
          placeholder="Search by ID or name"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All users</option>
          <option value="connected">Connected</option>
          <option value="disconnected">Disconnected</option>
          <option value="weak">Weak signal</option>
        </select>
        <span className="muted small">{visible.length} of {users.length} users</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>User ID</th>
              <th>User Name</th>
              <th>Connected AP</th>
              <th>Signal Strength</th>
              <th className="num">Distance</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((u) => (
              <tr key={u.id}>
                <td><strong>{u.id}</strong></td>
                <td>{u.name}</td>
                <td>{u.connected_ap || "-"}</td>
                <td>
                  <span className="dot" style={{ background: qualityColor(u.quality) }} />
                  {formatDbm(u.rssi)} <span className="muted small">{u.quality}</span>
                </td>
                <td className="num">{u.distance}</td>
                <td>
                  <span className={`badge ${u.status === "Connected" ? "badge-normal" : "badge-offline"}`}>
                    {u.status}
                  </span>
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr><td colSpan="6" className="muted">No users match the filter.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
