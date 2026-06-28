"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { apiFetchJSON } from "@/lib/api";
import { Layout } from "@/components/Layout";
import { StatusBadge } from "@/components/StatusBadge";
import { Pagination } from "@/components/Pagination";

interface Folder {
  id: string;
  external_id: string;
  state: string | null;
  registration_folder_external_id: string | null;
  amount_ttc: number | null;
  created_on: string | null;
  updated_on: string | null;
}

const states = [
  "",
  "toRegister",
  "registered",
  "toTake",
  "toRetake",
  "toControl",
  "success",
  "failed",
  "refused",
  "abort",
];

export default function CertificationFoldersPage() {
  const { user, loading: authLoading } = useAuth();
  const [folders, setFolders] = useState<Folder[]>([]);
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
        apiFetchJSON<Folder[]>(`/folders/certification?${params.toString()}`),
        apiFetchJSON<{ count: number }>(`/folders/certification/count?${params.toString()}`),
      ]);
      setFolders(listRes);
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
      <h1 style={{ marginTop: 0 }}>Sertifikasyon Dosyaları</h1>
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
              <th>Oluşturulma</th>
            </tr>
          </thead>
          <tbody>
            {folders.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty">
                  Kayıt bulunamadı.
                </td>
              </tr>
            ) : (
              folders.map((folder) => (
                <tr key={folder.id}>
                  <td>{folder.external_id}</td>
                  <td><StatusBadge state={folder.state} /></td>
                  <td>{folder.registration_folder_external_id ?? "—"}</td>
                  <td>{folder.amount_ttc?.toFixed(2) ?? "—"} €</td>
                  <td>
                    {folder.created_on
                      ? new Date(folder.created_on).toLocaleDateString("tr-TR")
                      : "—"}
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
