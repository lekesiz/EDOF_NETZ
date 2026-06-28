"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetchJSON, apiPost } from "@/lib/api";
import { Layout } from "@/components/Layout";

interface DashboardStats {
  target_amount: number;
  realized: number;
  remaining: number;
  kasa: number;
  alacak: number;
  kayip: number;
  total_dossiers: number;
  reconciled_count: number;
}

interface MonthlyData {
  month: string;
  kasa: number;
  alacak: number;
  kayip: number;
}

interface DashboardData {
  year: number;
  stats: DashboardStats;
  monthly_data: MonthlyData[];
  last_sync: Record<string, string | null>;
}

interface Setting {
  key: string;
  value: string;
  description: string | null;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("tr-TR");
}

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState<DashboardData | null>(null);
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  const canManage = user && ["superuser", "admin", "accountant"].includes(user.role);

  useEffect(() => {
    if (!authLoading && !user) {
      window.location.href = "/login";
      return;
    }
    if (user) {
      loadDashboard();
      loadSettings();
    }
  }, [authLoading, user, year]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const res = await apiFetchJSON<DashboardData>(`/dashboard?year=${year}`);
      setData(res);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      const res = await apiFetchJSON<Setting[]>("/dashboard/settings");
      setSettings(res);
    } catch {
      // ignore
    }
  };

  const updateSetting = async (key: string, value: string) => {
    try {
      await apiFetchJSON(`/dashboard/settings/${key}?value=${encodeURIComponent(value)}`, {
        method: "PUT",
      });
      await loadSettings();
      await loadDashboard();
      setMessage(`${key} güncellendi`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Hata oluştu");
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

  const targetValue = settings.find((s) => s.key === `target_${year}`)?.value || "0";
  const vadeValue = settings.find((s) => s.key === "vade_gun")?.value || "37";

  if (authLoading || loading) {
    return (
      <Layout>
        <p>Yükleniyor...</p>
      </Layout>
    );
  }
  if (!user) return null;

  const stats = data?.stats;
  const progress = stats && stats.target_amount > 0 ? (stats.realized / stats.target_amount) * 100 : 0;

  return (
    <Layout>
      <h1 style={{ marginTop: 0 }}>Dashboard</h1>
      {message && <div className="card" style={{ color: "var(--info)" }}>{message}</div>}

      <div className="toolbar">
        <select className="input" value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {[2025, 2026, 2027, 2028].map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <button className="btn btn-outline" onClick={loadDashboard}>Yenile</button>
      </div>

      {stats && (
        <>
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
              <div>
                <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Hedef CA</div>
                <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>{formatCurrency(stats.target_amount)}</div>
              </div>
              <div>
                <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Gerçekleşen</div>
                <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>{formatCurrency(stats.realized)}</div>
              </div>
              <div>
                <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Kalan</div>
                <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>{formatCurrency(stats.remaining)}</div>
              </div>
              <div style={{ minWidth: 200 }}>
                <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: 4 }}>
                  %{progress.toFixed(1)} tamamlandı
                </div>
                <div style={{ height: 10, background: "#e4e4e7", borderRadius: 5, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${Math.min(progress, 100)}%`,
                      height: "100%",
                      background: "var(--success)",
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="stats">
            <div className="stat">
              <div className="stat-value" style={{ color: "var(--success)" }}>{formatCurrency(stats.kasa)}</div>
              <div className="stat-label">Kasa (Échu)</div>
            </div>
            <div className="stat">
              <div className="stat-value" style={{ color: "var(--warning)" }}>{formatCurrency(stats.alacak)}</div>
              <div className="stat-label">Alacak (À venir)</div>
            </div>
            <div className="stat">
              <div className="stat-value" style={{ color: "var(--danger)" }}>{formatCurrency(stats.kayip)}</div>
              <div className="stat-label">Kayıp (İptal)</div>
            </div>
            <div className="stat">
              <div className="stat-value">{stats.total_dossiers}</div>
              <div className="stat-label">Toplam Dossier</div>
            </div>
            <div className="stat">
              <div className="stat-value">{stats.reconciled_count}</div>
              <div className="stat-label">Mutabakat</div>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Aylık Dağılım</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>Ay</th>
                  <th>Kasa</th>
                  <th>Alacak</th>
                  <th>Kayıp</th>
                  <th>Grafik</th>
                </tr>
              </thead>
              <tbody>
                {data?.monthly_data.map((m) => {
                  const total = m.kasa + m.alacak + m.kayip;
                  const max = Math.max(total, 1);
                  return (
                    <tr key={m.month}>
                      <td>{m.month}</td>
                      <td>{formatCurrency(m.kasa)}</td>
                      <td>{formatCurrency(m.alacak)}</td>
                      <td>{formatCurrency(m.kayip)}</td>
                      <td style={{ width: 200 }}>
                        <div style={{ display: "flex", height: 16, borderRadius: 4, overflow: "hidden", background: "#f4f4f5" }}>
                          <div style={{ width: `${(m.kasa / max) * 100}%`, background: "var(--success)" }} />
                          <div style={{ width: `${(m.alacak / max) * 100}%`, background: "var(--warning)" }} />
                          <div style={{ width: `${(m.kayip / max) * 100}%`, background: "var(--danger)" }} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {canManage && (
        <div className="card">
          <h3 className="card-title">Ayarlar</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: 4 }}>
                Hedef CA ({year})
              </label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  className="input"
                  type="number"
                  value={targetValue}
                  onChange={(e) =>
                    setSettings((prev) =>
                      prev.map((s) =>
                        s.key === `target_${year}` ? { ...s, value: e.target.value } : s
                      )
                    )
                  }
                />
                <button
                  className="btn"
                  onClick={() => updateSetting(`target_${year}`, targetValue)}
                >
                  Kaydet
                </button>
              </div>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: 4 }}>
                Vade Günü (bitiş + gün)
              </label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  className="input"
                  type="number"
                  value={vadeValue}
                  onChange={(e) =>
                    setSettings((prev) =>
                      prev.map((s) => (s.key === "vade_gun" ? { ...s, value: e.target.value } : s))
                    )
                  }
                />
                <button className="btn" onClick={() => updateSetting("vade_gun", vadeValue)}>
                  Kaydet
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h3 className="card-title">Senkronizasyon</h3>
        <div className="toolbar">
          <button
            className="btn"
            disabled={!canManage}
            onClick={() => runAction("Wedof senkronizasyonu", apiPost("/sync/wedof"))}
          >
            Wedof’u Senkronize Et
          </button>
          <button
            className="btn btn-outline"
            disabled={!canManage}
            onClick={() => runAction("Pennylane fatura çekme", apiPost("/pennylane/sync/invoices"))}
          >
            Pennylane Faturalarını Çek
          </button>
          <button
            className="btn btn-success"
            disabled={!canManage}
            onClick={() => (window.location.href = "/invoicing/daily")}
          >
            Günlük Faturalanacakları Gör
          </button>
        </div>
        {data?.last_sync && (
          <div style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.85rem" }}>
            <div>Son Wedof senkronizasyonu: {formatDateTime(data.last_sync.registration_folders)}</div>
            <div>Son Pennylane senkronizasyonu: {formatDateTime(data.last_sync.pennylane)}</div>
          </div>
        )}
      </div>
    </Layout>
  );
}
