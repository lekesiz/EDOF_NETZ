"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  version: string;
  database: string;
  redis: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setHealth(data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main style={{ padding: "2rem", maxWidth: "720px", margin: "0 auto" }}>
      <h1>EDOF-NETZ</h1>
      <p>CPF / EDOF yönetim ERP&apos;si</p>

      <section
        style={{
          marginTop: "2rem",
          padding: "1.5rem",
          borderRadius: "8px",
          background: "#f4f4f5",
        }}
      >
        <h2>Sistem Sağlığı</h2>
        {error && <p style={{ color: "red" }}>Hata: {error}</p>}
        {!health && !error && <p>Yükleniyor...</p>}
        {health && (
          <ul>
            <li>
              <strong>API:</strong> {health.status} ({health.version})
            </li>
            <li>
              <strong>PostgreSQL:</strong> {health.database}
            </li>
            <li>
              <strong>Redis:</strong> {health.redis}
            </li>
          </ul>
        )}
      </section>
    </main>
  );
}
