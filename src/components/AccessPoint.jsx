import { CONGESTION_COLORS } from "../utils";

// One Wi-Fi Access Point on the map: coverage circle + draggable Wi-Fi badge.
export default function AccessPoint({ ap, x, y, showRange, dragging, onPointerDown }) {
  const color = CONGESTION_COLORS[ap.congestion] || CONGESTION_COLORS.Normal;
  const ringRadii = [50, 100, 150].filter((r) => r < ap.coverage_range);

  return (
    <g className={`ap ${ap.online ? "" : "ap-off"}`}>
      {showRange && ap.online && (
        <g className="ap-range-group">
          <circle cx={x} cy={y} r={ap.coverage_range} className="ap-range" />
          {ringRadii.map((r) => (
            <circle key={r} cx={x} cy={y} r={r} className="ap-ring" />
          ))}
        </g>
      )}
      <g
        transform={`translate(${x}, ${y})`}
        className={`ap-badge ${dragging ? "dragging" : ""}`}
        onPointerDown={(e) => onPointerDown(ap, e)}
      >
        <title>{`${ap.id} - ${ap.name}\n${ap.connected_users}/${ap.capacity} users (${ap.utilization}%)\nDrag to move this access point`}</title>
        <circle r="17" fill={color} stroke="#fff" strokeWidth="3" />
        <g stroke="#fff" strokeWidth="1.9" fill="none" strokeLinecap="round">
          <path d="M-8 -2 A11 11 0 0 1 8 -2" />
          <path d="M-5 1.5 A7 7 0 0 1 5 1.5" />
        </g>
        <circle cx="0" cy="5.5" r="1.9" fill="#fff" />
        <g transform="translate(0, 31)">
          <rect x="-38" y="-10" width="76" height="19" rx="5" className="ap-label-bg" />
          <text textAnchor="middle" y="4" className="ap-label">
            {ap.online ? `${ap.id}  ${ap.connected_users}/${ap.capacity}` : `${ap.id}  OFF`}
          </text>
        </g>
      </g>
    </g>
  );
}
