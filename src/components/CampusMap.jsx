import { useRef, useState } from "react";
import AccessPoint from "./AccessPoint";
import UserMarker from "./UserMarker";
import { LEVEL_COLORS, QUALITY_COLORS, qualityColor, formatDbm } from "../utils";

const LEGEND = [
  ["Strong", "Strong"],
  ["Good", "Good"],
  ["Medium", "Medium"],
  ["Weak", "Weak"],
  ["No Connection", "Disconnected"],
];

// The 2D virtual campus, drawn with SVG (works offline, no map API needed).
export default function CampusMap({ campus, aps, users, heat, tickMs, onMoveAP }) {
  const svgRef = useRef(null);
  const [drag, setDrag] = useState(null); // { id, x, y, moved } while an AP is dragged
  const [selectedId, setSelectedId] = useState(null);
  const [opts, setOpts] = useState({ range: true, heat: false, lines: false, labels: false });

  if (!campus) return <div className="empty">Loading campus...</div>;

  const toggleOpt = (key) => setOpts((o) => ({ ...o, [key]: !o[key] }));

  // Convert a mouse position (screen pixels) into campus coordinates.
  const toCampusPoint = (e) => {
    const ctm = svgRef.current.getScreenCTM();
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(ctm.inverse());
    return {
      x: Math.min(Math.max(p.x, 10), campus.width - 10),
      y: Math.min(Math.max(p.y, 10), campus.height - 10),
    };
  };

  const handleApDown = (ap, e) => {
    e.stopPropagation();
    svgRef.current.setPointerCapture(e.pointerId);
    setDrag({ id: ap.id, x: ap.x, y: ap.y, moved: false });
  };
  const handleMove = (e) => {
    if (!drag) return;
    const p = toCampusPoint(e);
    setDrag((d) => (d ? { ...d, ...p, moved: true } : d));
  };
  const handleUp = async () => {
    if (!drag) return;
    const d = drag;
    try {
      if (d.moved) await onMoveAP(d.id, Math.round(d.x), Math.round(d.y));
    } finally {
      setDrag(null);
    }
  };

  const apPosition = (ap) => (drag && drag.id === ap.id ? { x: drag.x, y: drag.y } : { x: ap.x, y: ap.y });
  const selected = users.find((u) => u.id === selectedId) || null;
  const apById = Object.fromEntries(aps.map((a) => [a.id, a]));

  const connectionLines = users
    .filter((u) => u.connected_ap && (opts.lines || u.id === selectedId))
    .map((u) => {
      const ap = apById[u.connected_ap];
      if (!ap) return null;
      return (
        <line key={u.id} x1={u.x} y1={u.y} x2={ap.x} y2={ap.y}
              stroke={qualityColor(u.quality)} className="conn-line" />
      );
    });

  return (
    <div className="map-wrap">
      <div className="map-toolbar">
        {[["range", "Coverage circles"], ["heat", "Signal heat-map"], ["lines", "Connections"], ["labels", "User IDs"]].map(
          ([key, label]) => (
            <label key={key} className="check">
              <input type="checkbox" checked={opts[key]} onChange={() => toggleOpt(key)} />
              {label}
            </label>
          )
        )}
      </div>

      <svg
        ref={svgRef}
        className="campus-svg"
        viewBox={`0 0 ${campus.width} ${campus.height}`}
        onPointerMove={handleMove}
        onPointerUp={handleUp}
        onPointerCancel={() => setDrag(null)}
        onClick={() => setSelectedId(null)}
      >
        <rect x="0" y="0" width={campus.width} height={campus.height} className="campus-ground" />

        {campus.buildings.map((b) => (
          <g key={b.id}>
            <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={b.type === "building" ? 10 : 18}
                  fill={b.color} className={b.type === "building" ? "building" : "open-area"} />
            <text x={b.x + b.w / 2} y={b.y + (b.type === "building" ? 22 : 24)}
                  textAnchor="middle" className={b.type === "building" ? "building-name" : "open-name"}>
              {b.name}
            </text>
          </g>
        ))}

        {opts.heat && heat && (
          <g className="heat" pointerEvents="none">
            {heat.levels.map((lvl, i) => (
              <rect key={i} x={(i % heat.cols) * heat.cell} y={Math.floor(i / heat.cols) * heat.cell}
                    width={heat.cell} height={heat.cell} fill={LEVEL_COLORS[lvl]} />
            ))}
          </g>
        )}

        {connectionLines}

        {users.map((u) => (
          <UserMarker key={u.id} user={u} selected={u.id === selectedId} showLabel={opts.labels}
                      tickMs={tickMs} onSelect={setSelectedId} />
        ))}

        {aps.map((ap) => {
          const pos = apPosition(ap);
          return (
            <AccessPoint key={ap.id} ap={ap} x={pos.x} y={pos.y} showRange={opts.range}
                         dragging={!!drag && drag.id === ap.id} onPointerDown={handleApDown} />
          );
        })}
      </svg>

      <div className="map-footer">
        <div className="legend">
          {LEGEND.map(([key, label]) => (
            <span key={key} className="legend-item">
              <i style={{ background: QUALITY_COLORS[key] }} />
              {label}
            </span>
          ))}
        </div>
        <div className="selected-info">
          {selected ? (
            <>
              <strong>{selected.id} {selected.name}</strong>: {selected.connected_ap || "Disconnected"},{" "}
              {formatDbm(selected.rssi)}, {selected.quality}, {selected.distance} units
            </>
          ) : (
            "Click a user to inspect it. Drag an access point to move it."
          )}
        </div>
      </div>
    </div>
  );
}
