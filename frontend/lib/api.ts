const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type ApiFetchOptions = RequestInit & {
  skipJsonContentType?: boolean;
};

export async function apiFetch(path: string, options: ApiFetchOptions = {}) {
  const { headers, skipJsonContentType, ...rest } = options;
  const requestHeaders = new Headers(headers);

  if (!skipJsonContentType && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  return fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: requestHeaders,
    ...rest,
  });
}

export { API_BASE_URL };
