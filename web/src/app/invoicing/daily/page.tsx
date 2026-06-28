"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetchJSON, apiPost } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { StatusBadge } from "@/components/StatusBadge";
import { Pagination } from "@/components/Pagination";

interface Attendee {
  first_name: string | null;
  last_name: string | null;
  email: string | null;
}

interface Candidate {
  id: string;
  external_id: string;
  state: string | null;
  billing_state: string | null;
  amount_ttc: number | null;
  amount_ht: number | null;
  created_on: string | null;
  training_action_external_id: string | null;
  attendee: Attendee | null;
}

function formatDateInput(d: Date): string {
  return d.toLocaleDateString("fr-CA");
}

export default function DailyInvoicingPage() {
  const { user, loading: authLoading } = useAuth();
  const [date, setDate] = useState<string>(formatDateInput(new Date()));
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [pushing, setPushing] = useState<Set<string>>(new Set());

  const canManage = user && ["superuser", "admin", "accountant"].includes(user.role);

  useEffect(() => {
    if (!authLoading && !user) {
      window.location.href = "/login";
      return;
    }
    if (user) loadData();
  }, [authLoading, user, date, offset, limit]);

  const loadData = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const params = new URLSearchParams();
      params.set("date", date);
      params.set("limit", String(limit));
      params.set("offset", String(offset));
      const [listRes, countRes] = await Promise.all([
        apiFetchJSON<Candidate[]>(`/pennylane/candidates?${params.toString()}`),
        apiFetchJSON<{ count: number }>(`/pennylane/candidates/count?date=${encodeURIComponent(date)}`),
      ]);
      setCandidates(listRes);
      setCount(countRes.count);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  const pushInvoice = async (externalId: string) => {
    setPushing((prev) => new Set(prev).add(externalId));
    setMessage(`${externalId} için fatura oluşturuluyor...`);
    try {
      const res = await apiPost<{ task_id: string }>(
        `/pennylane/push/invoices/${encodeURIComponent(externalId)}?draft=true`
      );
      setMessage(`${externalId} için fatura oluşturma task’ı başlatıldı: ${res.task_id}`);
      await loadData();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Hata oluştu");
    } finally {
      setPushing((prev) => {
        const next = new Set(prev);
        next.delete(externalId);
        return next;
      });
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
      <h1 style={{ marginTop: 0 }}>Günlük Faturalanacaklar</h1>
      {message && <div className="card" style={{ color: "var(--info)" }}>{message}</div>}

      <div className="toolbar">
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          Tarih:
          <input
            className="input"
            type="date"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <span className="card" style={{ padding: "0.5rem 1rem" }}>
          {count} adet faturalanacak kayıt
        </span>
        <button className="btn btn-outline" onClick={loadData}>Yenile</button>
      </div>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>External ID</th>
              <th>Katılımcı</th>
              <th>Eğitim</th>
              <th>Durum</th>
              <th>Fatura Durumu</th>
              <th>Tutar (TTC)</th>
              <th>Oluşturulma</th>
              <th>İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {candidates.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty">
                  Bu tarih için faturalanacak kayıt bulunamadı.
                </td>
              </tr>
            ) : (
              candidates.map((candidate) => {
                const attendeeName = [
                  candidate.attendee?.first_name,
                  candidate.attendee?.last_name,
                ]
                  .filter(Boolean)
                  .join(" ") || "—";
                return (
                  <tr key={candidate.id}>
                    <td>{candidate.external_id}</td>
                    <td>
                      {attendeeName}
                      <br />
                      <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
                        {candidate.attendee?.email || "—"}
                      </span>
                    </td>
                    <td>{candidate.training_action_external_id || "—"}</td>
                    <td><StatusBadge state={candidate.state} /></td>
                    <td><StatusBadge state={candidate.billing_state} /></td>
                    <td>{candidate.amount_ttc?.toFixed(2) ?? "—"} €</td>
                    <td>
                      {candidate.created_on
                        ? new Date(candidate.created_on).toLocaleDateString("tr-TR")
                        : "—"}
                    </td>
                    <td>
                      <button
                        className="btn btn-success"
                        disabled={!canManage || pushing.has(candidate.external_id)}
                        onClick={() => pushInvoice(candidate.external_id)}
                      >
                        {pushing.has(candidate.external_id) ? "Gönderiliyor..." : "Fatura Oluştur"}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
        <Pagination offset={offset} limit={limit} total={count} onChange={setOffset} />
      </div>
    </Layout>
  );
}
