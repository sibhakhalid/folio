import { useState } from "react";
import { sendChat } from "./api.js";
import ChatPanel from "./components/ChatPanel.jsx";
import Stage from "./components/Stage.jsx";

let nextId = 1;
const newId = () => nextId++;

export default function App() {
  // Everything the UI needs lives in these four pieces of state.
  const [messages, setMessages] = useState([]); // chat bubbles
  const [versions, setVersions] = useState([]); // every PDF made: { pdfUrl, document }
  const [active, setActive] = useState(-1); // which version is shown on the right
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("chat"); // phones only: "chat" | "document"

  const currentVersion = versions[active] ?? null;

  async function handleSend(text) {
    const clean = text.trim();
    if (!clean || loading) return;

    // Last few messages give the AI context ("make it shorter" needs to know what "it" is).
    const history = messages.filter((m) => !m.error).slice(-8).map((m) => ({ role: m.role, text: m.text }));

    setMessages((prev) => [...prev, { id: newId(), role: "user", text: clean }]);
    setLoading(true);

    try {
      const data = await sendChat({
        message: clean,
        history,
        document: currentVersion?.document ?? null,
      });

      let versionNumber = null;
      if (data.pdf_url) {
        versionNumber = versions.length + 1;
        setVersions((prev) => [...prev, { pdfUrl: data.pdf_url, document: data.document }]);
        setActive(versions.length); // jump to the newest version
      }
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", text: data.reply, version: versionNumber, title: data.document?.title },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "assistant", text: err.message, error: true, retryText: clean },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function showVersion(versionNumber) {
    setActive(versionNumber - 1);
    setTab("document");
  }

  return (
    <div className="app" data-tab={tab}>
      <nav className="tabs" aria-label="Switch view">
        <button className={tab === "chat" ? "on" : ""} onClick={() => setTab("chat")}>
          Chat
        </button>
        <button className={tab === "document" ? "on" : ""} onClick={() => setTab("document")}>
          Document{versions.length > 0 && <span className="count">{versions.length}</span>}
        </button>
      </nav>

      <ChatPanel
        messages={messages}
        loading={loading}
        hasDocument={!!currentVersion}
        onSend={handleSend}
        onShowVersion={showVersion}
        activeVersion={active + 1}
      />

      <Stage
        versions={versions}
        active={active}
        onChangeActive={setActive}
        loading={loading}
      />
    </div>
  );
}
