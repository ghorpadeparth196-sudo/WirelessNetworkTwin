import NetworkStats, { CoverageSummary } from "./NetworkStats";
import CampusMap from "./CampusMap";
import Alerts from "./Alerts";
import APTable from "./APTable";

// The "Overview" page: cards, live campus map, alerts and the AP table.
export default function Dashboard({ state, campus, coverage, onMoveAP, onToggleAP }) {
  return (
    <>
      <div className="phase-banner">
        Campus activity: <strong>{state.phase}</strong>
      </div>
      <NetworkStats stats={state.stats} />
      <div className="grid-main">
        <section className="panel">
          <h2>Campus map</h2>
          <CampusMap
            campus={campus}
            aps={state.access_points}
            users={state.users}
            heat={coverage}
            tickMs={state.tick_ms}
            onMoveAP={onMoveAP}
          />
        </section>
        <aside className="side-column">
          <Alerts alerts={state.alerts} />
          <CoverageSummary coverage={state.stats.coverage} />
        </aside>
      </div>
      <section className="panel">
        <h2>Access points</h2>
        <APTable aps={state.access_points} onToggle={onToggleAP} />
      </section>
    </>
  );
}
