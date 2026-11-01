import { useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { ask } from "../api";

const EXAMPLES = [
  "Which site lost the most hours to rain this month?",
  "Rank sites by total labour hours in October",
  "Which sites have overdue milestones?",
  "How much did we spend on cement this month?",
];

function Result({ r }) {
  const [showSql, setShowSql] = useState(false);
  const { chart, columns, rows } = r;
  const data = rows.map((row) => Object.fromEntries(columns.map((c, i) => [c, row[i]])));
  return (
    <div className="result">
      <p className="answer">{r.answer}</p>
      {chart?.type !== "none" && data.length > 1 && (
        <div className="chart">
          <ResponsiveContainer>
            {chart.type === "line" ? (
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey={chart.x} fontSize={11} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Line dataKey={chart.y} stroke="#3b6fb6" strokeWidth={2} dot={false} />
              </LineChart>
            ) : (
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey={chart.x} fontSize={11} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis fontSize={11} />
                <Tooltip />
                <Bar dataKey={chart.y} fill="#3b6fb6" radius={[3, 3, 0, 0]} />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
      {r.ok && rows.length > 0 && (rows.length > 1 || columns.length > 1) && (
        <table>
          <thead><tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
          <tbody>{rows.slice(0, 10).map((row, i) => <tr key={i}>{row.map((v, j) => <td key={j}>{String(v)}</td>)}</tr>)}</tbody>
        </table>
      )}
      {r.sql && (
        <>
          <button className="link" onClick={() => setShowSql(!showSql)}>{showSql ? "hide" : "show"} SQL</button>
          {showSql && <pre>{r.sql}</pre>}
        </>
      )}
    </div>
  );
}

export default function AskBox() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState(null);
  const [err, setErr] = useState(null);

  const submit = (text) => {
    const question = (text ?? q).trim();
    if (!question) return;
    setQ(question);
    setLoading(true);
    setErr(null);
    ask(question).then(setRes).catch((e) => setErr(e.message)).finally(() => setLoading(false));
  };

  return (
    <div className="ask">
      <h3>Ask your data</h3>
      <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Which site lost the most hours to rain this month?" />
        <button disabled={loading}>{loading ? "Thinking…" : "Ask"}</button>
      </form>
      <div className="examples">
        {EXAMPLES.map((e) => <button key={e} className="chip-btn" onClick={() => submit(e)}>{e}</button>)}
      </div>
      {err && <div className="error">{err}</div>}
      {res && <Result r={res} />}
    </div>
  );
}
