/**
 * Cliente HTTP tipado contra el backend.
 *
 * Cambio Javier 2026-06-09: no hay API key por tenant. La admin
 * web pide:
 *   - X-Admin-Token (header, lo emite Yago)
 *   - tenantId (numérico — ej. 22 para San Fernando, sucursal del 20)
 * Ambos se guardan en localStorage para no preguntarlos cada refresh.
 */
import type {
  EmployeeListItem,
  EmployeeListResponse,
  EmployeeUpdatePayload,
  ImportSummary,
  TenantListResponse,
} from "@/types";

const BASE = "/api/v1";
const ADMIN_TOKEN_KEY = "qapp.adminToken";
const TENANT_ID_KEY = "qapp.tenantId";

export function getAdminToken(): string | null {
  return localStorage.getItem(ADMIN_TOKEN_KEY);
}
export function setAdminToken(token: string): void {
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
}

export function getTenantId(): number | null {
  const v = localStorage.getItem(TENANT_ID_KEY);
  return v ? Number(v) : null;
}
export function setTenantId(id: number): void {
  localStorage.setItem(TENANT_ID_KEY, String(id));
}

export function clearCredentials(): void {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
  localStorage.removeItem(TENANT_ID_KEY);
}

function adminHeaders(): Record<string, string> {
  const t = getAdminToken();
  return t ? { "X-Admin-Token": t } : {};
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
      headers: { ...adminHeaders() },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: no se pudo descargar la plantilla`);
    }
    return res.blob();
  },

  async importEmployees(file: File, tenantId: number): Promise<ImportSummary> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(
      `${BASE}/employees/import?tenantId=${tenantId}`,
      { method: "POST", headers: { ...adminHeaders() }, body: form }
    );
    return unwrap<ImportSummary>(res);
  },

  async listEmployees(
    tenantId: number,
    params?: {
      limit?: number;
      offset?: number;
      q?: string;
      tenantName?: string | null;
    }
  ): Promise<EmployeeListResponse> {
    const qs = new URLSearchParams();
    qs.set("tenantId", String(tenantId));
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    if (params?.q) qs.set("q", params.q);
    if (params?.tenantName !== undefined && params.tenantName !== null) {
      // cadena vacía = "empleados sin nombre de tenant" (backend
      // acepta explícitamente ese caso — no lo confundas con "no
      // enviar el param", que es tenantName === null / undefined).
      qs.set("tenantName", params.tenantName);
    }
    const res = await fetch(`${BASE}/employees?${qs.toString()}`, {
      headers: { ...adminHeaders() },
    });
    return unwrap<EmployeeListResponse>(res);
  },

  async listTenants(tenantId: number): Promise<TenantListResponse> {
    const qs = new URLSearchParams({ tenantId: String(tenantId) });
    const res = await fetch(
      `${BASE}/employees/tenants?${qs.toString()}`,
      { headers: { ...adminHeaders() } }
    );
    return unwrap<TenantListResponse>(res);
  },

  async updateEmployee(
    tenantId: number,
    employeeId: number,
    payload: EmployeeUpdatePayload
  ): Promise<EmployeeListItem> {
    const qs = new URLSearchParams({ tenantId: String(tenantId) });
    const res = await fetch(
      `${BASE}/employees/${employeeId}?${qs.toString()}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...adminHeaders(),
        },
        body: JSON.stringify(payload),
      }
    );
    return unwrap<EmployeeListItem>(res);
  },

  async deleteEmployee(
    tenantId: number,
    employeeId: number
  ): Promise<void> {
    const qs = new URLSearchParams({ tenantId: String(tenantId) });
    const res = await fetch(
      `${BASE}/employees/${employeeId}?${qs.toString()}`,
      { method: "DELETE", headers: { ...adminHeaders() } }
    );
    if (!res.ok && res.status !== 204) {
      let detail: string;
      try {
        const data = await res.json();
        detail = data?.detail || JSON.stringify(data);
      } catch {
        detail = await res.text();
      }
      throw new Error(`HTTP ${res.status}: ${detail}`);
    }
  },
};
