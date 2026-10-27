import { Bar, Legend, StatTile, fmt, signed } from "./ui.jsx";

const MATCH = [
  { key: "correct", icon: "✓", label: "Correct", status: "good", help: "Found, right vehicle type" },
  { key: "wrong_type", icon: "⇄", label: "Wrong type", status: "warning", help: "Found, but called the wrong type" },
  { key: "missed", icon: "✕", label: "Missed", status: "critical", help: "Real vehicle the model did not find" },
  { key: "extra", icon: "+", label: "Extra", status: "serious", help: "Model box with no real vehicle (false alarm)" },
];

function Diff({ d, digits = 2 }) {
  if (d.difference === 0) return <span className="muted">0</span>;
  return <span>{signed(d.difference, digits)}</span>;
}

function sourceText(c) {
  if (c.source === "uploaded") return "Correct answers from your uploaded label file.";
  return `Correct answers found automatically (${c.split} split of the dataset).`;
}

export default function Comparison({ comparison: c }) {
  const m = c.matching;
  const total = m.correct + m.wrong_type + m.missed;
  const o = c.overall;
  const maxCount = Math.max(...c.by_class.flatMap((k) => [k.count.predicted, k.count.actual]), 0);

  return (
    <>
      <section className="card">
        <h2>Actual vs predicted</h2>
        <p className="muted">{sourceText(c)}</p>
        {c.split === "train" && (
          <div className="alert warning" role="note">
            ⚠ The model studied this photo during training, so it is not a fair test. Use a photo from the test
            split instead.
          </div>
        )}

        <div className="match-row">
          {MATCH.map((s) => (
            <div key={s.key} className={`match status-${s.status}`} title={s.help}>
              <span className="match-icon" aria-hidden="true">{s.icon}</span>
              <span className="match-value num">{m[s.key]}</span>
              <span className="match-label">{s.label}</span>
            </div>
          ))}
        </div>
        <p className="muted small">
          The model found {m.correct + m.wrong_type} of {total} real vehicles ({m.correct} with the right type).
          Boxes count as the same vehicle when they overlap by at least 50%.
        </p>
        {m.wrong_type_details.length > 0 && (
          <ul className="small">
            {m.wrong_type_details.map((w, i) => (
              <li key={i}>
                Real <b>{w.actual}</b> called <b>{w.predicted}</b>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="tiles">
        <StatTile
          label="PCU error"
          value={o.pcu_error_pct === null ? "–" : `${fmt(o.pcu_error_pct, 1)}%`}
          sub={`predicted ${fmt(o.pcu.predicted)} vs actual ${fmt(o.pcu.actual)}`}
        />
        <StatTile
          label="Density difference"
          value={signed(o.density.difference)}
          sub={`predicted ${fmt(o.density.predicted)} vs actual ${fmt(o.density.actual)}`}
        />
        <StatTile
          label="Vehicle difference"
          value={signed(o.vehicles.difference, 0)}
          sub={`predicted ${o.vehicles.predicted} vs actual ${o.vehicles.actual}`}
        />
        <StatTile
          label="Avg lane PCU error"
          value={fmt(o.lane_pcu_mae)}
          sub="average PCU off per lane"
        />
      </section>

      <div className="grid-2">
        <section className="card">
          <div className="card-head">
            <h2>Per vehicle type</h2>
            <Legend items={[{ label: "Predicted", series: 1 }, { label: "Actual", series: 2 }]} />
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Vehicle</th>
                <th className="num">Predicted</th>
                <th className="num">Actual</th>
                <th className="num">Diff</th>
                <th className="bar-col" aria-label="Count bars" />
              </tr>
            </thead>
            <tbody>
              {c.by_class.map((k) => (
                <tr key={k.class_id}>
                  <td>{k.label}</td>
                  <td className="num">{k.count.predicted}</td>
                  <td className="num">{k.count.actual}</td>
                  <td className="num"><Diff d={k.count} digits={0} /></td>
                  <td className="bar-col">
                    <div className="bar-pair">
                      <Bar value={k.count.predicted} max={maxCount} series={1}
                           tip={`${k.label}: predicted ${k.count.predicted}`} />
                      <Bar value={k.count.actual} max={maxCount} series={2}
                           tip={`${k.label}: actual ${k.count.actual}`} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card">
          <h2>Per lane (PCU)</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Lane</th>
                <th className="num">Predicted</th>
                <th className="num">Actual</th>
                <th className="num">Diff</th>
              </tr>
            </thead>
            <tbody>
              {c.lanes.map((l) => (
                <tr key={l.zone}>
                  <td>Lane {l.zone + 1}</td>
                  <td className="num">{fmt(l.pcu.predicted)}</td>
                  <td className="num">{fmt(l.pcu.actual)}</td>
                  <td className="num"><Diff d={l.pcu} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </>
  );
}
