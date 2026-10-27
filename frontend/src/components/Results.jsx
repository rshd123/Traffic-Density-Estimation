import { useState } from "react";
import { Bar, StatTile, fmt } from "./ui.jsx";

function downloadJson(data) {
  const blob = new Blob([JSON.stringify(data.result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${(data.result.image || "result").replace(/\.[^.]+$/, "")}_density.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function ImageView({ data }) {
  const actual = data.comparison?.actual_image;
  const [view, setView] = useState("predicted");
  const showActual = view === "actual" && actual;

  return (
    <section className="card">
      <div className="card-head">
        <h2>Result photo</h2>
        {actual && (
          <div className="segmented small" role="radiogroup" aria-label="Which boxes to show">
            {["predicted", "actual"].map((v) => (
              <button
                key={v}
                type="button"
                role="radio"
                aria-checked={view === v}
                className={view === v ? "active" : ""}
                onClick={() => setView(v)}
              >
                {v === "predicted" ? "Predicted (model)" : "Actual (correct answers)"}
              </button>
            ))}
          </div>
        )}
      </div>
      <img
        className="result-img"
        src={showActual ? actual : data.image}
        alt={showActual ? "Road photo with the correct vehicle boxes and lanes" : "Road photo with detected vehicles and lanes"}
      />
      <p className="muted small">
        White lines = virtual lanes (L1 = far left). Red tint = PCU density: the stronger the red, the denser the
        lane. Each box shows the vehicle type and its PCU.
      </p>
    </section>
  );
}

export default function Results({ data }) {
  const r = data.result;
  const o = r.overall;
  const maxDensity = Math.max(...r.zones.map((z) => z.density), 0);
  const maxPcu = Math.max(...r.by_class.map((c) => c.pcu), 0);

  return (
    <>
      <ImageView data={data} />

      <section className="tiles">
        <StatTile label="Vehicles" value={fmt(o.vehicles, 0)} sub="cars, bikes, autos, buses, trucks on the road" />
        <StatTile label="Total PCU" value={fmt(o.pcu)} sub="vehicles weighted by size (car = 1)" />
        <StatTile
          label="PCU density"
          value={fmt(o.density)}
          sub={`plain count density: ${fmt(o.count_density)}`}
          help="Total PCU ÷ road area (area measured as a share of the photo)"
        />
        <StatTile
          label="Busiest lane"
          value={o.busiest_zone === null ? "–" : `Lane ${o.busiest_zone + 1}`}
          sub={o.busiest_zone === null ? "no vehicles found" : `${fmt(r.zones[o.busiest_zone].pcu)} PCU`}
        />
      </section>

      <div className="grid-2">
        <section className="card">
          <h2>Density per lane</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Lane</th>
                <th className="num">Vehicles</th>
                <th className="num">PCU</th>
                <th className="num">Density</th>
                <th className="bar-col" aria-label="Density bar" />
              </tr>
            </thead>
            <tbody>
              {r.zones.map((z) => (
                <tr key={z.zone}>
                  <td>
                    Lane {z.zone + 1}
                    {o.busiest_zone === z.zone && <span className="tag">busiest</span>}
                  </td>
                  <td className="num">{z.vehicles}</td>
                  <td className="num">{fmt(z.pcu)}</td>
                  <td className="num">{fmt(z.density)}</td>
                  <td className="bar-col">
                    <Bar value={z.density} max={maxDensity} tip={`Lane ${z.zone + 1}: density ${fmt(z.density)}`} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card">
          <h2>By vehicle type</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Vehicle</th>
                <th className="num">Count</th>
                <th className="num">PCU</th>
                <th className="bar-col" aria-label="PCU bar" />
              </tr>
            </thead>
            <tbody>
              {r.by_class.map((c) => (
                <tr key={c.class_id}>
                  <td>{c.label}</td>
                  <td className="num">{c.count}</td>
                  <td className="num">{fmt(c.pcu)}</td>
                  <td className="bar-col">
                    <Bar value={c.pcu} max={maxPcu} tip={`${c.label}: ${c.count} vehicles = ${fmt(c.pcu)} PCU`} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {r.off_road > 0 && (
            <p className="muted small">{r.off_road} vehicle(s) above the horizon were left out.</p>
          )}
        </section>
      </div>

      <div className="actions">
        <button type="button" onClick={() => downloadJson(data)}>Download result (JSON)</button>
      </div>
    </>
  );
}
