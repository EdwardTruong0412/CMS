export interface ApiErrorItem {
  field: string | null;
  code: string;
  params: Record<string, unknown>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public errors: ApiErrorItem[],
  ) {
    super("API request failed");
    this.name = "ApiError";
  }
}

export class SystemClosedError extends Error {
  constructor() {
    super("System is closed");
    this.name = "SystemClosedError";
  }
}

const closedListeners = new Set<() => void>();

export function onSystemClosed(listener: () => void): () => void {
  closedListeners.add(listener);
  return () => {
    closedListeners.delete(listener);
  };
}

function systemClosed(): never {
  for (const listener of closedListeners) listener();
  throw new SystemClosedError();
}

function isApiErrorItem(value: unknown): value is ApiErrorItem {
  return (
    typeof value === "object" &&
    value !== null &&
    "field" in value &&
    (value.field === null || typeof value.field === "string") &&
    "code" in value &&
    typeof value.code === "string" &&
    "params" in value &&
    typeof value.params === "object" &&
    value.params !== null &&
    !Array.isArray(value.params)
  );
}

export async function apiRequest<T>(
  path: `/api/${string}`,
  options?: {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    body?: unknown;
  },
): Promise<T> {
  const method = options?.method ?? "GET";
  const headers = new Headers({ Accept: "application/json" });
  const body =
    options?.body === undefined ? undefined : JSON.stringify(options.body);
  if (body !== undefined) headers.set("Content-Type", "application/json");
  if (method !== "GET") headers.set("X-CMS-Request", "1");

  let response: Response;
  try {
    response = await fetch(path, {
      method,
      credentials: "same-origin",
      headers,
      body,
    });
  } catch {
    return systemClosed();
  }
  if (response.status === 503) return systemClosed();
  if (!response.ok) {
    let errors: ApiErrorItem[] = [];
    try {
      const payload: unknown = await response.json();
      if (
        typeof payload === "object" &&
        payload !== null &&
        "errors" in payload &&
        Array.isArray(payload.errors) &&
        payload.errors.every(isApiErrorItem)
      ) {
        errors = payload.errors;
      }
    } catch {
      // Proxies can return HTML or an empty body instead of API JSON.
    }
    throw new ApiError(response.status, errors);
  }
  if (response.status === 204) return undefined as T;
  const payload: unknown = await response.json();
  return payload as T;
}

export interface StatusOut {
  status: "open";
}

export function getStatus(): Promise<StatusOut> {
  return apiRequest<StatusOut>("/api/v1/status");
}
