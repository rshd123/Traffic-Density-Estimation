// Small shared pieces: stat tile, inline bar, legend, number formatting.

export const fmt = (n, digits = 2) =>
  n === null || n === undefined ? "–" : Number(n).toLocaleString(undefined, { maximumFractionDigits: digits });

export const signed = (n, digits = 2) => (n > 0 ? "+" : "") + fmt(n, digits);

export function StatTile({ label, value, sub, help }) {
  return (
    <div className="tile" title={help}>
      <span className="tile-label">{label}</span>
      <span className="tile-value num">{value}</span>
      {sub && <span className="tile-sub muted small">{sub}</span>}
    </div>
  );
}

// Horizontal bar scaled to max; tip shows on hover / keyboard focus.
export function Bar({ value, max, series = 1, tip }) {
  const pct = max > 0 ? Math.max((value / max) * 100, value > 0 ? 1.5 : 0) : 0;
  return (
    <div className="bar-track" tabIndex={0} data-tip={tip} aria-label={tip}>
      <div className={`bar series-${series}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Legend({ items }) {
  return (
    <div className="legend">
      {items.map((it) => (
        <span key={it.label} className="legend-item">
          <span className={`swatch series-${it.series}`} />
          {it.label}
        </span>
      ))}
    </div>
  );
}
