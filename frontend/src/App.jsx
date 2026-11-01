import { useEffect, useState } from "react";
import { getSites, STATUS } from "./api";
import SiteMap from "./components/SiteMap";
import SitePanel from "./components/SitePanel";
import AskBox from "./components/AskBox";

export default function App() {
  const [sites, setSites] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getSites().then(setSites).catch((e) => setError(e.message));
  }, []);

  const counts = Object.keys(STATUS).map((k) => ({ k, n: sites.filter((s) => s.status === k).length }));

  return (
    <div className="app">
      <header>
        <h1>Site Control Room</h1>
        <div className="legend">
          {counts.map(({ k, n }) => (
            <span key={k} className="chip">
              <i style={{ background: STATUS[k].color }} /> {STATUS[k].label} <b>{n}</b>
            </span>
          ))}
        </div>
      </header>
      {error && <div className="error">Could not load sites: {error}. Is the API running on :8000?</div>}
      <main>
        <section className="left">
          <SiteMap sites={sites} selectedId={selected} onSelect={setSelected} />
          <AskBox />
        </section>
        <aside className="right">
          {selected ? (
            <SitePanel siteId={selected} />
          ) : (
            <div className="placeholder">Select a pin on the map to see progress, photos, labour and the weekly summary.</div>
          )}
        </aside>
      </main>
    </div>
  );
}
