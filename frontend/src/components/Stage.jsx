import { useEffect, useState } from "react";
import { downloadPdf, openUrl, previewUrl } from "../api.js";

function slugify(text) {
  return (text || "document").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 50) || "document";
}

export default function Stage({ versions, active, onChangeActive, loading }) {
  const version = versions[active];
  const [dl, setDl] = useState("idle"); // idle | loading | done | error

  // Reset the download button when switching versions.
  useEffect(() => setDl("idle"), [active]);

  async function handleDownload() {
    setDl("loading");
    try {
      await downloadPdf(version.pdfUrl, slugify(version.document?.title));
      setDl("done");
      setTimeout(() => setDl("idle"), 2500);
    } catch {
      setDl("error");
    }
  }

  const dlLabel = { idle: "Download PDF", loading: "Downloading…", done: "Saved", error: "Failed, retry" }[dl];

  return (
    <section className="stage" aria-label="Document preview">
      <div className="stage-bar">
        {version ? (
          <>
            <div className="stepper">
              <button onClick={() => onChangeActive(active - 1)} disabled={active <= 0} aria-label="Previous version">
                ‹
              </button>
              <span>
                Version {active + 1} <em>of {versions.length}</em>
              </span>
              <button onClick={() => onChangeActive(active + 1)} disabled={active >= versions.length - 1} aria-label="Next version">
                ›
              </button>
            </div>
            <div className="actions">
              <a className="ghost" href={openUrl(version.pdfUrl)} target="_blank" rel="noreferrer">
                Open
              </a>
              <button className={"primary " + dl} onClick={handleDownload} disabled={dl === "loading"}>
                {dlLabel}
              </button>
            </div>
          </>
        ) : (
          <span className="stage-hint">Preview</span>
        )}
      </div>

      <div className="desk">
        <div className={"sheet" + (loading ? " busy" : "") + (!version && !loading ? " blank" : "")}>
          {version && <iframe key={version.pdfUrl} title="PDF preview" src={previewUrl(version.pdfUrl)} />}

          {!version && !loading && (
            <div className="blank-note">
              <p>Your PDF appears here.</p>
              <span>Every change you ask for becomes a new version you can step back to.</span>
            </div>
          )}

          {loading && (
            <div className="skeleton" aria-hidden="true">
              <div className="sk title" />
              <div className="sk line w90" />
              <div className="sk line w70" />
              <div className="sk gap" />
              <div className="sk head" />
              <div className="sk line w95" />
              <div className="sk line w85" />
              <div className="sk line w60" />
              <div className="sk block" />
              <div className="sk line w90" />
              <div className="sk line w75" />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
