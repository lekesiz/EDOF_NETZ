"use client";

import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

export default function Home() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      window.location.href = user ? "/dashboard" : "/login";
    }
  }, [user, loading]);

  return (
    <main style={{ padding: "2rem", textAlign: "center" }}>
      <p>Yönlendiriliyor...</p>
    </main>
  );
}
