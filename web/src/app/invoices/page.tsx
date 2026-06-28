"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetchJSON } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { StatusBadge } from "@/components/StatusBadge";
import { Pagination } from "@/components/Pagination";

interface Invoice {
  id: string;
  external_id: string | null;
  state: string | null;
  amount_ttc: number | null;
  amount_ht: number | null;
  due_date: string | null;
  registration_folder_external_id: string | null;
  pennylane_customer_id: string | null;
  pennylane_invoice_id: string | null;
}

const states = ["", "draft", "finalized", "paid", "billed", "imported"];

export default function InvoicesPage() {
  const { user, loading: authLoading } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [state, setState] = useState("");
  const [search, setSearch] = useState("");
  const [limit] = useState(25);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

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
        apiFetchJSON<Invoice[]>(`/invoices?${params.toString()}`),
        apiFetchJSON<{ count: number }>(`/invoices/count?${params.toString()}`),
      ]);
      setInvoices(listRes);
      setCount(countRes.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yüklenemedi");
    } finally {
      setLoading(false);
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
      <h1 style={{ marginTop: 0 }}>Faturalar</h1>
      {error && <p className="error">{error}</p>}

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

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>External ID</th>
              <th>Durum</th>
              <th>Kayıt Dosyası</th>
              <th>Tutar (TTC)</th>
              <th>Tutar (HT)</th>
              <th>Son Ödeme</th>
              <th>Pennylane ID</th>
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty">
                  Kayıt bulunamadı.
                </td>
              </tr>
            ) : (
              invoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td>{invoice.external_id ?? "—"}</td>
                  <td><StatusBadge state={invoice.state} /></td>
                  <td>{invoice.registration_folder_external_id ?? "—"}</td>
                  <td>{invoice.amount_ttc?.toFixed(2) ?? "—"} €</td>
                  <td>{invoice.amount_ht?.toFixed(2) ?? "—"} €</td>
                  <td>
                    {invoice.due_date
                      ? new Date(invoice.due_date).toLocaleDateString("tr-TR")
                      : "—"}
                  </td>
                  <td>{invoice.pennylane_invoice_id ?? "—"}</td>
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
