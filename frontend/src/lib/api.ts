const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "dev-api-key";

interface RequestOptions extends RequestInit {
  actor?: string;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { actor, headers, ...rest } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      "X-Actor": actor ?? "frontend-user",
      ...(headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail ?? detail;
    } catch {
      // keep status text fallback
    }
    throw new Error(`${response.status}: ${detail}`);
  }

  return response.json() as Promise<T>;
}
