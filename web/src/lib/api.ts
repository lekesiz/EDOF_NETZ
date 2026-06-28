const API_BASE = "/api";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("edof_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem("edof_token", token);
  } else {
    localStorage.removeItem("edof_token");
  }
}

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
}

export async function apiFetchJSON<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await apiFetch(path, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiFetchJSON<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}
