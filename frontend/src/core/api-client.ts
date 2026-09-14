const BASE_URL = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (
    resp.status === 401 &&
    path !== "/auth/login" &&
    path !== "/auth/refresh"
  ) {
    const refreshResp = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (refreshResp.ok) {
      const retried = await fetch(`${BASE_URL}${path}`, {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      if (!retried.ok) throw new Error(`HTTP ${retried.status}`);
      return retried.json() as Promise<T>;
    }
    throw new Error("HTTP 401");
  }

  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path: string) =>
    fetch(`${BASE_URL}${path}`, { method: "DELETE", credentials: "include" }),
};
