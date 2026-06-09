/**
 * Cliente HTTP tipado contra el backend. Auth por X-Tenant-Key,
 * la key se guarda en localStorage para no preguntarla cada refresh.
 */
import type { EmployeeListResponse, ImportSummary } from "@/types";

const BASE = "/api/v1";
const TENANT_KEY_STORAGE = "qapp.tenantKey";

export function getTenantKey(): string | null {
  return localStorage.getItem(TENANT_KEY_STORAGE);
}

export function setTenantKey(key: string): void {
  localStorage.setItem(TENANT_KEY_STORAGE, key);
}

export function clearTenantKey(): void {
  localStorage.removeItem(TENANT_KEY_STORAGE);
}

function authHeaders(): Record<string, string> {
  const key = getTenantKey();
  return key ? { "X-Tenant-Key": key } : {};
}

async function unwrap<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail: string;
    try {
      const data = await res.json();
      detail = data?.detail || JSON.stringify(data);
    } catch {
      detail = await res.text();
    }
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async downloadTemplate(): Promise<Blob> {
    const res = await fetch(`${BASE}/employees/template.xlsx`, {
      headers: { ...authHeaders() },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: no se pudo descargar la plantilla`);
    }
    return res.blob();
  },

  async importEmployees(file: File): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/employees/import`, {
      method: "POST",
      headers: { ...authHeaders() },
      body: form,
    });
    return unwrap<ImportSummary>(res);
  },

  async listEmployees(params?: {
    limit?: number;
    offset?: number;
    q?: string;
  }): Promise<EmployeeListResponse> {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    if (params?.q) qs.set("q", params.q);
    const res = await fetch(`${BASE}/employees?${qs.toString()}`, {
      headers: { ...authHeaders() },
    });
    return unwrap<EmployeeListResponse>(res);
  },
};
