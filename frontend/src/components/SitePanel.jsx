import { useEffect, useState } from "react";
import {
  ResponsiveContainer, ComposedChart, BarChart, Bar, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid,
} from "recharts";
import { getSite, getSummary, STATUS, inr } from "../api";

const fmt = (d) => (d ? new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "—");

function Timeline({ milestones, asOf }) {
  return (
    <ol className="timeline">
      {milestones.map((m) => {
        const done = !!m.actual_date;
        const overdue = !done && m.planned_date < asOf;
        const late = done && m.actual_date > m.planned_date;
        return (
          <li key={m.name} className={done ? "done" : overdue ? "overdue" : "upcoming"}>
            <span className="dot" />
            <div>
              <b>{m.name}</b>
              <small>
                planned {fmt(m.planned_date)}
                {done && ` · done ${fmt(m.actual_date)}${late ? " (late)" : ""}`}
                {overdue && " · overdue"}
              </small>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export default function SitePanel({ siteId }) {
  const [d, setD] = useState(null);
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setD(null);
    setSummary(null);
    getSite(siteId).then(setD);
    getSummary(siteId).then((r) => setSummary(r.summary)).catch(() => setSummary("Summary unavailable."));
  }, [siteId]);

  if (!d) return <div className="placeholder">Loading…</div>;
  const { site } = d;
  const st = STATUS[site.status];

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>{site.name}</h2>
        <span className="badge" style={{ background: st.color }}>{st.label}</span>
      </div>
      <div className="meta">{site.city} · budget {inr(site.budget_inr)} · due {fmt(site.planned_end)}</div>

      <div className="progress">
        <div className="bar">
          <div className="plan" style={{ width: `${site.planned_pct}%` }} />
          <div className="actual" style={{ width: `${site.progress_pct}%`, background: st.color }} />
        </div>
        <small>{Number(site.progress_pct)}% complete · schedule says {Number(site.planned_pct)}%</small>
      </div>

      <h3>Weekly summary <span className="ai">AI</span>
        <button className="link" disabled={busy} onClick={() => {
          setBusy(true);
          getSummary(siteId, true).then((r) => setSummary(r.summary)).finally(() => setBusy(false));
        }}>regenerate</button>
      </h3>
      <p className="summary">{summary ?? "Writing summary…"}</p>

      <h3>Progress timeline</h3>
      <Timeline milestones={d.milestones} asOf={d.as_of} />

      <h3>Labour and rain, last 12 weeks</h3>
      <div className="chart">
        <ResponsiveContainer>
          <ComposedChart data={d.labour_weekly}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="week" fontSize={11} />
            <YAxis yAxisId="l" fontSize={11} />
            <YAxis yAxisId="r" orientation="right" fontSize={11} />
            <Tooltip />
            <Legend />
            <Bar yAxisId="l" dataKey="hours_worked" name="Labour hours" fill="#3b6fb6" radius={[3, 3, 0, 0]} />
            <Line yAxisId="r" dataKey="rain_hours_lost" name="Rain hours lost" stroke="#d64545" strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <h3>Material spend to date</h3>
      <div className="chart small">
        <ResponsiveContainer>
          <BarChart data={d.material_cost} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" fontSize={11} tickFormatter={(v) => inr(v)} />
            <YAxis type="category" dataKey="material" fontSize={11} width={70} />
            <Tooltip formatter={(v) => inr(v)} />
            <Bar dataKey="cost_inr" fill="#8a6bbf" radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <h3>Photos</h3>
      <div className="gallery">
        {d.photos.map((p) => (
          <figure key={p.url}>
            <img src={p.url} alt={p.caption} loading="lazy" />
            <figcaption>{p.caption} · {fmt(p.taken_on)}</figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
