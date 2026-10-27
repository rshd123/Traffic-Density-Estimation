import { useRef, useState } from "react";

const IMAGE_TYPES = "image/jpeg,image/png,image/webp,image/bmp";

export default function UploadPanel({ file, labels, onFile, onLabels }) {
  const input = useRef(null);
  const [dragging, setDragging] = useState(false);

  function drop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFile(f);
  }

  return (
    <section className="card">
      <h2>1. Road photo</h2>
      <button
        type="button"
        className={`dropzone${dragging ? " dragging" : ""}`}
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={drop}
      >
        <span className="dropzone-title">{file ? file.name : "Drop a photo here"}</span>
        <span className="muted small">{file ? "Click to pick another" : "or click to choose (jpg, png, webp)"}</span>
      </button>
      <input
        ref={input}
        type="file"
        accept={IMAGE_TYPES}
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />

      <label className="field">
        <span>Correct answers (optional)</span>
        <input
          type="file"
          accept=".txt"
          onChange={(e) => onLabels(e.target.files?.[0] || null)}
        />
        <span className="muted small">
          {labels
            ? `Using ${labels.name}`
            : "YOLO label file (.txt). Photos from data/subset are matched automatically."}
        </span>
      </label>
    </section>
  );
}
