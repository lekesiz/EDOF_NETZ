"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/folders/registration", label: "Kayıt Dosyaları" },
  { href: "/folders/certification", label: "Sertifikasyon Dosyaları" },
  { href: "/attendees", label: "Katılımcılar" },
  { href: "/invoices", label: "Faturalar" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">EDOF-NETZ</div>
        <nav className="sidebar-nav">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-link ${pathname === item.href ? "active" : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <div>
            <strong>{user?.full_name || user?.email}</strong>
            <span style={{ color: "var(--muted)", marginLeft: "0.5rem" }}>
              ({user?.role})
            </span>
          </div>
          <button onClick={logout} className="btn btn-danger">
            Çıkış Yap
          </button>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
