export interface ImportError {
  row: number;
  column: string | null;
  reason: string;
}

export interface ImportSummary {
  received: number;
  inserted: number;
  updated: number;
  failed: number;
  errors: ImportError[];
}

export interface EmployeeListItem {
  id: number;
  tenantId: number;
  tenantName: string | null;
  employeeCode: string;
  documentNumber: string;
  documentType: string;
  fullName: string;
  /** "Active" o "Inactive" — string libre del backend */
  status: string;
  statusReason: string | null;
  /** Tope de consumo en céntimos; null = sin tope. */
  purchaseLimitCents: number | null;
  updatedAt: string;
}

export interface EmployeeListResponse {
  total: number;
  items: EmployeeListItem[];
}

export interface EmployeeUpdatePayload {
  employeeCode?: string;
  documentNumber?: string;
  documentType?: string;
  fullName?: string;
  status?: string;
  statusReason?: string | null;
  tenantName?: string | null;
  purchaseLimitCents?: number | null;
}

export interface TenantSummary {
  tenantName: string | null;
  count: number;
}

export interface TenantListResponse {
  items: TenantSummary[];
}

export interface AdminTokenRequestResponse {
  success: boolean;
  message: string;
}

export interface PurchaseRow {
  id: number;
  employeeId: number;
  employeeName: string;
  employeeCode: string;
  documentNumber: string;
  amountCents: number;
  currency: string;
  purchasedAt: string;
  kioskName: string | null;
}

export interface PurchaseListResponse {
  total: number;
  totalCents: number;
  currency: string;
  items: PurchaseRow[];
}
