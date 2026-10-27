const LANE_OPTIONS = [3, 5, 7];

export default function SettingsPanel({ settings, onChange, onRun, canRun, stale }) {
  const set = (key) => (e) => onChange({ ...settings, [key]: Number(e.target.value) });

  return (
    <section className="card">
      <h2>2. Settings</h2>

      <div className="field">
        <span>Lanes</span>
        <div className="segmented" role="radiogroup" aria-label="Number of lanes">
          {LANE_OPTIONS.map((n) => (
            <button
              key={n}
              type="button"
              role="radio"
              aria-checked={settings.numZones === n}
              className={settings.numZones === n ? "active" : ""}
              onClick={() => onChange({ ...settings, numZones: n })}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      <label className="field">
        <span>
          Confidence <b className="num">{Math.round(settings.conf * 100)}%</b>
        </span>
        <input type="range" min="0.05" max="0.9" step="0.05" value={settings.conf} onChange={set("conf")} />
        <span className="muted small">Only keep vehicles the model is at least this sure about.</span>
      </label>

      <label className="field">
        <span>
          Horizon height <b className="num">{Math.round(settings.horizonY * 100)}%</b>
        </span>
        <input type="range" min="0.2" max="0.8" step="0.01" value={settings.horizonY} onChange={set("horizonY")} />
        <span className="muted small">Where the road disappears, measured from the top of the photo.</span>
      </label>

      <button type="button" className="primary" onClick={onRun} disabled={!canRun}>
        {stale ? "Run again with new settings" : "Run again"}
      </button>
    </section>
  );
}
