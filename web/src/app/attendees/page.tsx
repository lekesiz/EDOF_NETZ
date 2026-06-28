"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetchJSON } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { Pagination } from "@/components/Pagination";

interface Attendee {
  id: string;
  wedof_id: number | null;
  pennylane_customer_id: string | null;
  email: string | null;
  first_name: string | null;
  last_name: string | null;
  phone_number: string | null;
}

export default function AttendeesPage() {
  const { user, loading: authLoading } = useAuth();
  const [attendees, setAttendees] = useState<Attendee[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
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
  }, [authLoading, user, search, offset, limit]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(limit));
      params.set("offset", String(offset));
      if (search) params.set("search", search);
      const [listRes, countRes] = await Promise.all([
        apiFetchJSON<Attendee[]>(`/folders/attendees?${params.toString()}`),
        apiFetchJSON<{ count: number }>(`/folders/attendees/count?${params.toString()}`),
      ]);
      setAttendees(listRes);
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
      <h1 style={{ marginTop: 0 }}>Katılımcılar</h1>
      {error && <p className="error">{error}</p>}

      <div className="toolbar">
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
              <th>Ad Soyad</th>
              <th>Email</th>
              <th>Telefon</th>
              <th>Wedof ID</th>
              <th>Pennylane Müşteri ID</th>
            </tr>
          </thead>
          <tbody>
            {attendees.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty">
                  Kayıt bulunamadı.
                </td>
              </tr>
            ) : (
              attendees.map((attendee) => (
                <tr key={attendee.id}>
                  <td>
                    {attendee.first_name || attendee.last_name
                      ? `${attendee.first_name || ""} ${attendee.last_name || ""}`.trim()
                      : "—"}
                  </td>
                  <td>{attendee.email ?? "—"}</td>
                  <td>{attendee.phone_number ?? "—"}</td>
                  <td>{attendee.wedof_id ?? "—"}</td>
                  <td>{attendee.pennylane_customer_id ?? "—"}</td>
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
