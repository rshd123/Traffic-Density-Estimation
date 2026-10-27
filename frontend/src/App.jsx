import { useEffect, useRef, useState } from "react";
import { analyze, getConfig } from "./api.js";
import UploadPanel from "./components/UploadPanel.jsx";
import SettingsPanel from "./components/SettingsPanel.jsx";
import Results from "./components/Results.jsx";
import Comparison from "./components/Comparison.jsx";

const FALLBACK = { conf: 0.25, numZones: 5, horizonY: 0.42 };

export default function App() {
  const [pcu, setPcu] = useState([]);
  const [settings, setSettings] = useState(FALLBACK);
  const [file, setFile] = useState(null);
  const [labels, setLabels] = useState(null);
  const [data, setData] = useState(null);
  const [ranWith, setRanWith] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const runId = useRef(0);

  useEffect(() => {
    getConfig()
      .then((c) => {
        setPcu(c.pcu);
        setSettings({ conf: c.conf, numZones: c.lanes.num_zones, horizonY: c.lanes.horizon_y });
      })
      .catch((e) => setError(e.message));
  }, []);

  async function run(nextFile = file, nextLabels = labels) {
    if (!nextFile) return;
    const id = ++runId.current;
    setLoading(true);
    setError("");
    try {
      const res = await analyze(nextFile, nextLabels, settings);
      if (id !== runId.current) return; // a newer run started
      setData(res);
      setRanWith({ ...settings, labels: nextLabels });
    } catch (e) {
      if (id === runId.current) setError(e.message);
    } finally {
      if (id === runId.current) setLoading(false);
    }
  }

  function pickFile(f) {
    setFile(f);
    setData(null);
    run(f, labels);
  }

  function pickLabels(f) {
    setLabels(f);
    if (file) run(file, f);
  }

  const stale =
    data &&
    ranWith &&
    (ranWith.conf !== settings.conf ||
      ranWith.numZones !== settings.numZones ||
      ranWith.horizonY !== settings.horizonY);

  return (
    <div className="page">
      <header className="header">
        <h1>Traffic Density Estimation</h1>
        <p>Upload a road photo → PCU-weighted traffic density for each lane.</p>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <UploadPanel file={file} labels={labels} onFile={pickFile} onLabels={pickLabels} />
          <SettingsPanel
            settings={settings}
            onChange={setSettings}
            onRun={() => run()}
            canRun={!!file && !loading}
            stale={stale}
          />
          {pcu.length > 0 && (
            <section className="card">
              <h2>PCU weights</h2>
              <p className="muted small">How much road one vehicle takes, compared with one car.</p>
              <table className="table compact">
                <tbody>
                  {pcu.map((p) => (
                    <tr key={p.class_id}>
                      <td>{p.label}</td>
                      <td className="num">{p.pcu}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </aside>

        <main className="main">
          {error && <div className="alert error" role="alert">{error}</div>}
          {loading && <div className="alert info">Analysing photo…</div>}
          {!data && !loading && !error && (
            <div className="empty">
              <p>Pick a road photo on the left to see its traffic density.</p>
              <p className="muted small">
                Tip: photos from <code>data/subset/test/images</code> also show the correct answers, so you can
                compare actual vs predicted.
              </p>
            </div>
          )}
          {data && (
            <>
              <Results data={data} />
              {data.comparison ? (
                <Comparison comparison={data.comparison} />
              ) : (
                <section className="card">
                  <h2>Actual vs predicted</h2>
                  <p className="muted">
                    No correct answers for this photo. Upload its label file (.txt) on the left, or use a photo
                    from <code>data/subset/test/images</code>.
                  </p>
                </section>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
