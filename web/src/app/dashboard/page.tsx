"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetchJSON, apiPost } from "@/lib/api";
import { Layout } from "@/components/Layout";

interface Counts {
  registration: number;
  certification: number;
  attendees: number;
  invoices: number;
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [counts, setCounts] = useState<Counts | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  const canManage = user && ["superuser", "admin", "accountant"].includes(user.role);

  useEffect(() => {
    if (!authLoading && !user) {
      window.location.href = "/login";
      return;
    }
    if (user) {
      loadCounts();
    }
  }, [authLoading, user]);

  const loadCounts = async () => {
    setLoading(true);
    try {
      const [registration, certification, attendees, invoices] = await Promise.all([
        apiFetchJSON<{ count: number }>("/folders/registration/count"),
        apiFetchJSON<{ count: number }>("/folders/certification/count"),
        apiFetchJSON<{ count: number }>("/folders/attendees/count"),
        apiFetchJSON<{ count: number }>("/invoices/count"),
      ]);
      setCounts({
        registration: registration.count,
        certification: certification.count,
        attendees: attendees.count,
        invoices: invoices.count,
      });
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  const runAction = async (label: string, promise: Promise<{ task_id: string }>) => {
    setMessage(`${label} başlatıldı...`);
    try {
      const res = await promise;
      setMessage(`${label} başlatıldı. Task ID: ${res.task_id}`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Hata oluştu");
    }
  };

  if (authLoading || loading) {
    return (
      <Layout>
        <p>Yükleniyor...</p>
      </Layout>
    );
  }
  if (!user) return null;

  return (
    <Layout>
      <h1 style={{ marginTop: 0 }}>Dashboard</h1>

      {message && <div className="card" style={{ color: "var(--info)" }}>{message}</div>}

      <div className="stats">
        <div className="stat">
          <div className="stat-value">{counts?.registration ?? "—"}</div>
          <div className="stat-label">Kayıt Dosyası</div>
        </div>
        <div className="stat">
          <div className="stat-value">{counts?.certification ?? "—"}</div>
          <div className="stat-label">Sertifikasyon Dosyası</div>
        </div>
        <div className="stat">
          <div className="stat-value">{counts?.attendees ?? "—"}</div>
          <div className="stat-label">Katılımcı</div>
        </div>
        <div className="stat">
          <div className="stat-value">{counts?.invoices ?? "—"}</div>
          <div className="stat-label">Fatura</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Senkronizasyon İşlemleri</h2>
        <div className="toolbar">
          <button
            className="btn"
            disabled={!canManage}
            onClick={() => runAction("Wedof senkronizasyonu", apiPost("/sync/wedof"))}
          >
            Wedof’u Senkronize Et
          </button>
          <button
            className="btn btn-success"
            disabled={!canManage}
            onClick={() =>
              runAction("Pennylane fatura gönderimi", apiPost("/pennylane/push/invoices"))
            }
          >
            Faturaları Pennylane’e Gönder
          </button>
          <button
            className="btn btn-outline"
            disabled={!canManage}
            onClick={() =>
              runAction("Pennylane fatura çekme", apiPost("/pennylane/sync/invoices"))
            }
          >
            Pennylane Faturalarını Çek
          </button>
        </div>
        {!canManage && (
          <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
            Senkronizasyon işlemleri için admin, superuser veya accountant rolü gerekir.
          </p>
        )}
      </div>
    </Layout>
  );
}
