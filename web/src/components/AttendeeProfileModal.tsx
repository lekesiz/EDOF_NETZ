"use client";

import { useEffect, useState } from "react";
import { apiFetchJSON } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";

interface Attendee {
  id: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone_number: string | null;
  wedof_id: number | null;
}

interface Folder {
  id: string;
  external_id: string;
  state: string | null;
  billing_state: string | null;
  amount_ttc: number | null;
  created_on: string | null;
}

interface Invoice {
  id: string;
  external_id: string | null;
  state: string | null;
  amount_ttc: number | null;
  amount_ht: number | null;
  due_date: string | null;
  registration_folder_external_id: string | null;
  pennylane_invoice_id: string | null;
}

interface Profile {
  attendee: Attendee;
  registration_folders: Folder[];
  certification_folders: Folder[];
  invoices: Invoice[];
}

interface AttendeeProfileModalProps {
  attendeeId: string | null;
  onClose: () => void;
}

export function AttendeeProfileModal({ attendeeId, onClose }: AttendeeProfileModalProps) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!attendeeId) {
      setProfile(null);
      return;
    }
    setLoading(true);
    setError(null);
    apiFetchJSON<Profile>(`/folders/attendees/${encodeURIComponent(attendeeId)}/profile`)
      .then(setProfile)
      .catch((err) => setError(err instanceof Error ? err.message : "Yüklenemedi"))
      .finally(() => setLoading(false));
  }, [attendeeId]);

  if (!attendeeId) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 8,
          width: "100%",
          maxWidth: 900,
          maxHeight: "90vh",
          overflow: "auto",
          boxShadow: "0 20px 40px rgba(0,0,0,0.2)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            padding: "1.25rem",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            position: "sticky",
            top: 0,
            background: "#fff",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "1.2rem" }}>Katılımcı Profili</h2>
          <button onClick={onClose} className="btn btn-outline">
            Kapat
          </button>
        </div>

        <div style={{ padding: "1.25rem" }}>
          {loading && <p>Yükleniyor...</p>}
          {error && <p className="error">{error}</p>}
          {!loading && profile && (
            <div className="space-y-6">
              <div className="card">
                <h3 className="card-title">Kişisel Bilgiler</h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.75rem" }}>
                  <div>
                    <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Ad Soyad</div>
                    <div style={{ fontWeight: 600 }}>
                      {profile.attendee.first_name} {profile.attendee.last_name}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>E-posta</div>
                    <div>{profile.attendee.email || "—"}</div>
                  </div>
                  <div>
                    <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Telefon</div>
                    <div>{profile.attendee.phone_number || "—"}</div>
                  </div>
                  <div>
                    <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Wedof ID</div>
                    <div>{profile.attendee.wedof_id ?? "—"}</div>
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="card-title">
                  Kayıt Dosyaları ({profile.registration_folders.length})
                </h3>
                {profile.registration_folders.length === 0 ? (
                  <p style={{ color: "var(--muted)" }}>Kayıt dosyası yok.</p>
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>External ID</th>
                        <th>Durum</th>
                        <th>Fatura Durumu</th>
                        <th>Tutar</th>
                        <th>Oluşturulma</th>
                      </tr>
                    </thead>
                    <tbody>
                      {profile.registration_folders.map((folder) => (
                        <tr key={folder.id}>
                          <td>{folder.external_id}</td>
                          <td><StatusBadge state={folder.state} /></td>
                          <td><StatusBadge state={folder.billing_state} /></td>
                          <td>{folder.amount_ttc?.toFixed(2) ?? "—"} €</td>
                          <td>
                            {folder.created_on
                              ? new Date(folder.created_on).toLocaleDateString("tr-TR")
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="card">
                <h3 className="card-title">
                  Sertifikasyon Dosyaları ({profile.certification_folders.length})
                </h3>
                {profile.certification_folders.length === 0 ? (
                  <p style={{ color: "var(--muted)" }}>Sertifikasyon dosyası yok.</p>
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>External ID</th>
                        <th>Durum</th>
                        <th>Tutar</th>
                        <th>Oluşturulma</th>
                      </tr>
                    </thead>
                    <tbody>
                      {profile.certification_folders.map((folder) => (
                        <tr key={folder.id}>
                          <td>{folder.external_id}</td>
                          <td><StatusBadge state={folder.state} /></td>
                          <td>{folder.amount_ttc?.toFixed(2) ?? "—"} €</td>
                          <td>
                            {folder.created_on
                              ? new Date(folder.created_on).toLocaleDateString("tr-TR")
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="card">
                <h3 className="card-title">Faturalar ({profile.invoices.length})</h3>
                {profile.invoices.length === 0 ? (
                  <p style={{ color: "var(--muted)" }}>Fatura yok.</p>
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Pennylane ID</th>
                        <th>Kayıt Dosyası</th>
                        <th>Durum</th>
                        <th>Tutar (TTC)</th>
                        <th>Son Ödeme</th>
                      </tr>
                    </thead>
                    <tbody>
                      {profile.invoices.map((invoice) => (
                        <tr key={invoice.id}>
                          <td>{invoice.pennylane_invoice_id ?? "—"}</td>
                          <td>{invoice.registration_folder_external_id ?? "—"}</td>
                          <td><StatusBadge state={invoice.state} /></td>
                          <td>{invoice.amount_ttc?.toFixed(2) ?? "—"} €</td>
                          <td>
                            {invoice.due_date
                              ? new Date(invoice.due_date).toLocaleDateString("tr-TR")
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
