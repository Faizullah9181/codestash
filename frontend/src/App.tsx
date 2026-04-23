import { useEffect, useState } from "react";

import { apiGet } from "./lib/api";

export default function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    apiGet<{ service: string; status: string }>("/api/status")
      .then((data) => setStatus(`${data.service}: ${data.status}`))
      .catch(() => setStatus("backend unreachable"));
  }, []);

  return (
    <main className="app-shell">
      <section className="card">
        <h1>CodeStash Starterpack</h1>
        <p>Reusable frontend + backend + terraform + actions base.</p>
        <p><strong>API:</strong> {status}</p>
      </section>
    </main>
  );
}
