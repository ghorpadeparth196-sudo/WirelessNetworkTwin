import { qualityColor, formatDbm } from "../utils";

// One virtual student on the map. The CSS transition on "transform" makes the
// dot glide smoothly from its old position to the new one every tick.
export default function UserMarker({ user, selected, showLabel, tickMs, onSelect }) {
  const color = qualityColor(user.quality);
  const tooltip =
    `${user.id} - ${user.name}\n` +
    `AP: ${user.connected_ap || "none (disconnected)"}\n` +
    `Signal: ${formatDbm(user.rssi)} (${user.quality})\n` +
    `Distance: ${user.distance}`;

  return (
    <g
      className="user"
      style={{
        transform: `translate(${user.x}px, ${user.y}px)`,
        transitionDuration: `${tickMs}ms`,
      }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(user.id);
      }}
    >
      <title>{tooltip}</title>
      {selected && <circle r="13" fill="none" stroke={color} strokeWidth="2" opacity="0.6" />}
      <circle r={selected ? 8 : 6} fill={color} stroke="#fff" strokeWidth={selected ? 2.5 : 1.5} />
      {(showLabel || selected) && (
        <text y="-12" textAnchor="middle" className="user-label">
          {user.id}
        </text>
      )}
    </g>
  );
}
