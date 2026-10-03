import { useEffect, useRef, useState } from "react";

// Example prompts shown before the first message. Clicking one sends it.
const STARTERS = [
  "A one-page project proposal for a neighbourhood food-sharing app",
  "Turn my meeting notes into a clean summary with action items",
  "A weekly sales report with a comparison table by region",
  "A formal leave policy for a 20-person company",
];

// Quick edits shown once a document exists.
const QUICK_EDITS = [
  { label: "Shorter", prompt: "Make it shorter. Keep only the essentials." },
  { label: "More professional", prompt: "Make it more professional and formal." },
  { label: "New colors", prompt: "Change the color scheme to something fresh that suits the topic." },
  { label: "Different layout", prompt: "Switch to a different layout style." },
  { label: "Add a summary", prompt: "Add a short executive summary at the start." },
];

export default function ChatPanel({ messages, loading, hasDocument, onSend, onShowVersion, activeVersion }) {
  const [text, setText] = useState("");
  const listRef = useRef(null);
  const inputRef = useRef(null);

  // Keep the newest message in view.
  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  // Grow the text box as the user types (up to a limit).
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 220) + "px";
  }, [text]);

  function submit() {
    if (!text.trim() || loading) return;
    onSend(text);
    setText("");
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  const empty = messages.length === 0;

  return (
    <section className="chat" aria-label="Chat">
      <header className="brand">
        <span className="logo" aria-hidden="true" />
        <span className="wordmark">Folio</span>
      </header>

      <div className="messages" ref={listRef} aria-live="polite">
        {empty ? (
          <div className="intro">
            <h1>Say it messy. Get it designed.</h1>
            <p>Describe the document you need, or paste your raw notes. I'll organise them into a finished PDF.</p>
            <ul className="starters">
              {STARTERS.map((s) => (
                <li key={s}>
                  <button onClick={() => onSend(s)}>{s}</button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          messages.map((m) => (
            <Message key={m.id} m={m} onShowVersion={onShowVersion} activeVersion={activeVersion} onRetry={onSend} loading={loading} />
          ))
        )}

        {loading && (
          <div className="msg assistant">
            <div className="typing" role="status" aria-label="Working on your document">
              <i /> <i /> <i />
              <span>Writing and laying out your PDF</span>
            </div>
          </div>
        )}
      </div>

      <div className="composer-wrap">
        {hasDocument && !loading && (
          <div className="chips" aria-label="Quick edits">
            {QUICK_EDITS.map((q) => (
              <button key={q.label} onClick={() => onSend(q.prompt)}>
                {q.label}
              </button>
            ))}
          </div>
        )}
        <div className="composer">
          <textarea
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder={hasDocument ? "Ask for a change, e.g. make the headings green" : "Describe your PDF or paste your notes"}
            aria-label="Message"
            disabled={loading}
          />
          <button className="send" onClick={submit} disabled={loading || !text.trim()} aria-label="Send">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
      </div>
    </section>
  );
}

function Message({ m, onShowVersion, activeVersion, onRetry, loading }) {
  if (m.role === "user") {
    return (
      <div className="msg user">
        <p>{m.text.length > 900 ? m.text.slice(0, 900) + "…" : m.text}</p>
      </div>
    );
  }
  return (
    <div className={"msg assistant" + (m.error ? " error" : "")}>
      <p>{m.text}</p>
      {m.version && (
        <button className={"docchip" + (activeVersion === m.version ? " current" : "")} onClick={() => onShowVersion(m.version)}>
          <span className="mini" aria-hidden="true" />
          <span className="docchip-text">
            <b>{m.title || "Document"}</b>
            <small>Version {m.version}</small>
          </span>
        </button>
      )}
      {m.error && m.retryText && (
        <button className="retry" onClick={() => onRetry(m.retryText)} disabled={loading}>
          Try again
        </button>
      )}
    </div>
  );
}
