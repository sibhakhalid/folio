// api.js: the only file that talks to the backend.
// Notice there is NO API key here. The browser only knows our own server.

const API_BASE = import.meta.env.VITE_API_URL || ""; // "" = same origin (Vite proxies /api in dev)

export async function sendChat({ message, history, document }) {
  let res;
  try {
    res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history, document }),
    });
  } catch {
    throw new Error("Can't reach the server. Is the backend running on port 8000?");
  }

  if (!res.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
      else if (res.status === 422) detail = "That message couldn't be processed. It may be too long.";
    } catch {
      /* response wasn't JSON, keep the default message */
    }
    throw new Error(detail);
  }
  return res.json(); // { reply, document, pdf_id, pdf_url }
}

export function previewUrl(pdfUrl) {
  // The #fragment asks the browser's PDF viewer to hide its toolbar and fit the page width.
  return `${API_BASE}${pdfUrl}#toolbar=0&navpanes=0&view=FitH`;
}

export function openUrl(pdfUrl) {
  return `${API_BASE}${pdfUrl}`;
}

export async function downloadPdf(pdfUrl, name) {
  const res = await fetch(`${API_BASE}${pdfUrl}?download=1&name=${encodeURIComponent(name)}`);
  if (!res.ok) throw new Error("Download failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${name}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
