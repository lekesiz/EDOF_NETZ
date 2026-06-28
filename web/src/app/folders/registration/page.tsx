"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetchJSON, apiPost } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { StatusBadge } from "@/components/StatusBadge";
import { Pagination } from "@/components/Pagination";
import { AttendeeProfileModal } from "@/components/AttendeeProfileModal";

interface Folder {
  id: string;
  external_id: string;
  attendee_id: string | null;
  state: string | null;
  billing_state: string | null;
  amount_ttc: number | null;
  created_on: string | null;
  is_reconciled: boolean;
  pennylane_invoice_number: string | null;
  pennylane_paid_date: string | null;
  wedof_paid_date: string | null;
}

const CANCEL_KEYWORDS = ["cancel", "refus", "reject", "annul", "abandon"];

function isInvalidated(status: string | null): boolean {
  if (!status) return false;
  const lower = status.toLowerCase();
  return CANCEL_KEYWORDS.some((kw) => lower.includes(kw));
}

function getPaymentBadge(folder: Folder) {
  if (isInvalidated(folder.state)) {
    return <span className="badge badge-danger">İptal</span>;
  }
  if (folder.is_reconciled || folder.pennylane_paid_date) {
    return <span className="badge badge-success">Payé Pennylane</span>;
  }
  if (folder.wedof_paid_date) {
    return <span className="badge badge-info">Payé Wedof</span>;
  }
  return <span className="badge badge-warning">Bekliyor</span>;
}

const states = [
  "",
  "notProcessed",
  "validated",
  "waitingAcceptation",
  "accepted",
  "inTraining",
  "terminated",
  "serviceDoneDeclared",
  "serviceDoneValidated",
  "canceledByAttendee",
  "canceledByOrganism",
  "canceledByFinancer",
  "refusedByAttendee",
  "refusedByOrganism",
  "refusedByFinancer",
  "rejected",
];

export default function RegistrationFoldersPage() {
  const { user, loading: authLoading } = useAuth();
  const [folders, setFolders] = useState<Folder[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState("");
  const [search, setSearch] = useState("");
  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedAttendeeId, setSelectedAttendeeId] = useState<string | null>(null);

  const canManage = user && ["superuser", "admin", "accountant"].includes(user.role);

  useEffect(() => {
    if (!authLoading && !user) {
      window.location.href = "/login";
      return;
    }
    if (user) loadData();
  }, [authLoading, user, state, search, offset, limit]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(limit));
      params.set("offset", String(offset));
      if (state) params.set("state", state);
      if (search) params.set("search", search);
      const [listRes, countRes] = await Promise.all([
        apiFetchJSON<Folder[]>(`/folders/registration?${params.toString()}`),
        apiFetchJSON<{ count: number }>(`/folders/registration/count?${params.toString()}`),
      ]);
      setFolders(listRes);
      setCount(countRes.count);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  const pushInvoice = async (externalId: string) => {
    setMessage(`${externalId} faturası gönderiliyor...`);
    try {
      const res = await apiPost<{ task_id: string }>(
        `/pennylane/push/invoices/${encodeURIComponent(externalId)}?draft=true`
      );
      setMessage(`${externalId} için task başlatıldı: ${res.task_id}`);
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
      <h1 style={{ marginTop: 0 }}>Kayıt Dosyaları</h1>
      {message && <div className="card" style={{ color: "var(--info)" }}>{message}</div>}

      <div className="toolbar">
        <select className="input" value={state} onChange={(e) => { setState(e.target.value); setOffset(0); }}>
          {states.map((s) => (
            <option key={s} value={s}>
              {s || "Tüm Durumlar"}
            </option>
          ))}
        </select>
        <input
          className="input"
          type="text"
          placeholder="Ara..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
        />
        <button className="btn btn-outline" onClick={loadData}>Yenile</button>
      </div>

      <AttendeeProfileModal
        attendeeId={selectedAttendeeId}
        onClose={() => setSelectedAttendeeId(null)}
      />

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>External ID</th>
              <th>Katılımcı</th>
              <th>Durum</th>
              <th>Fatura Durumu</th>
              <th>Ödeme</th>
              <th>Tutar (TTC)</th>
              <th>Oluşturulma</th>
              <th>İşlemler</th>
            </tr>
          </thead>
          <tbody>
            {folders.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty">
                  Kayıt bulunamadı.
                </td>
              </tr>
            ) : (
              folders.map((folder) => (
                <tr
                  key={folder.id}
                  style={{ cursor: folder.attendee_id ? "pointer" : "default" }}
                  onClick={() => folder.attendee_id && setSelectedAttendeeId(folder.attendee_id)}
                >
                  <td>{folder.external_id}</td>
                  <td>
                    {folder.attendee_id ? (
                      <span style={{ color: "var(--info)", textDecoration: "underline" }}>
                        Profili Gör
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td><StatusBadge state={folder.state} /></td>
                  <td><StatusBadge state={folder.billing_state} /></td>
                  <td>{getPaymentBadge(folder)}</td>
                  <td>{folder.amount_ttc?.toFixed(2) ?? "—"} €</td>
                  <td>
                    {folder.created_on
                      ? new Date(folder.created_on).toLocaleDateString("tr-TR")
                      : "—"}
                  </td>
                  <td>
                    <button
                      className="btn btn-success"
                      disabled={!canManage}
                      onClick={(e) => {
                        e.stopPropagation();
                        pushInvoice(folder.external_id);
                      }}
                    >
                      Fatura Gönder
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <Pagination offset={offset} limit={limit} total={count} onChange={setOffset} />
      </div>
    </Layout>
  );
}
