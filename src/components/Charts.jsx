import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, Tooltip, Legend, Filler,
} from "chart.js";
import { CONGESTION_COLORS } from "../utils";

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend, Filler);

const base = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,              // charts refresh every second, so no animation
  plugins: { legend: { position: "bottom" } },
};

// Four live charts. They re-render whenever the simulation state changes.
export default function Charts({ aps, history }) {
  const labels = aps.map((a) => a.id);
  const timeLabels = history.map((h) => `t${h.tick}`);

  const usersPerAp = {
    labels,
    datasets: [
      { label: "Connected users", data: aps.map((a) => a.connected_users), backgroundColor: "#1b7f8c" },
      { label: "Capacity", data: aps.map((a) => a.capacity), backgroundColor: "#cdd6df" },
    ],
  };

  const utilization = {
    labels,
    datasets: [{
      label: "Utilization (%)",
      data: aps.map((a) => a.utilization),
      backgroundColor: aps.map((a) => CONGESTION_COLORS[a.congestion] || "#1b7f8c"),
    }],
  };

  const signal = {
    labels: timeLabels,
    datasets: [{
      label: "Average signal (dBm)",
      data: history.map((h) => h.avg_signal),
      borderColor: "#2c5aa0", backgroundColor: "rgba(44,90,160,0.12)",
      fill: true, tension: 0.3, pointRadius: 0, spanGaps: true,
    }],
  };

  const congestion = {
    labels: timeLabels,
    datasets: [
      { label: "Average utilization (%)", data: history.map((h) => h.avg_utilization),
        borderColor: "#1b7f8c", backgroundColor: "rgba(27,127,140,0.12)",
        fill: true, tension: 0.3, pointRadius: 0 },
      { label: "Busiest AP (%)", data: history.map((h) => h.max_utilization),
        borderColor: "#d9433b", tension: 0.3, pointRadius: 0 },
    ],
  };

  return (
    <div className="chart-grid">
      <section className="panel">
        <h2>Users per Access Point</h2>
        <div className="chart-box">
          <Bar data={usersPerAp} options={{ ...base, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }} />
        </div>
      </section>
      <section className="panel">
        <h2>AP Utilization</h2>
        <div className="chart-box">
          <Bar data={utilization}
               options={{ ...base, plugins: { legend: { display: false } },
                          scales: { y: { beginAtZero: true, suggestedMax: 100, title: { display: true, text: "%" } } } }} />
        </div>
      </section>
      <section className="panel">
        <h2>Average Signal Strength</h2>
        <div className="chart-box">
          <Line data={signal}
                options={{ ...base, scales: { y: { min: -90, max: -30, title: { display: true, text: "dBm" } } } }} />
        </div>
      </section>
      <section className="panel">
        <h2>Network Congestion over Time</h2>
        <div className="chart-box">
          <Line data={congestion}
                options={{ ...base, scales: { y: { beginAtZero: true, suggestedMax: 100, title: { display: true, text: "%" } } } }} />
        </div>
      </section>
    </div>
  );
}
