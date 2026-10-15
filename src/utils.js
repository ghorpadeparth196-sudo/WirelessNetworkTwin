// Colours and small helpers shared by several components.
export const QUALITY_COLORS = {
  Strong: "#1a9e55",
  Good: "#7bc043",
  Medium: "#e8b923",
  Weak: "#d9433b",
  "No Connection": "#8d96a3",
};

// Used by the coverage heat-map: numeric level -> colour
export const LEVEL_COLORS = ["#8d96a3", "#d9433b", "#e8b923", "#7bc043", "#1a9e55"];

export const CONGESTION_COLORS = {
  Normal: "#1b7f8c",
  Moderate: "#e8b923",
  High: "#f08a24",
  Overloaded: "#d9433b",
  Offline: "#8d96a3",
};

export const qualityColor = (quality) => QUALITY_COLORS[quality] || QUALITY_COLORS["No Connection"];

export const formatDbm = (value) =>
  value === null || value === undefined ? "-" : `${Math.round(value)} dBm`;
